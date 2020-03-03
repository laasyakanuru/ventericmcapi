import json
import os
from datetime import date, datetime, timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework_swagger.views import get_swagger_view
from rest_framework.response import Response
from rest_framework.views import APIView

from Backend.settings import MEDIA_ROOT
from Venter.models import (Category, File, Organisation, UserCategory,
                           UserComplaint)
from Venter.serializers import (CategorySerializer, FileSerializer,
                                OrganisationSerializer)

from .ML_Model.ICMC.model.ClassificationService import ClassificationService
from .wordcloud import generate_wordcloud


class OrganisationViewSet(viewsets.ModelViewSet):
    queryset = Organisation.objects
    serializer_class = OrganisationSerializer

    @classmethod
    def list(cls, request):
        """
            OrganisationViewSet for getting a list of organisations associated with the application
        """
        queryset = Organisation.objects.all()

        # Serialize and return
        serialized = OrganisationSerializer(queryset, context={'get': 'list'}, many=True).data

        return Response(serialized)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects
    serializer_class = CategorySerializer

    @classmethod
    def list(cls, request):
        """
            CategoryViewSet for getting a list of categories present in all organisations registered with the application
        """
        queryset = Category.objects.all()

        # Serialize and return
        serialized = CategorySerializer(queryset, context={'get': 'list'}, many=True).data

        return Response(serialized)

    @classmethod
    def retrieve(cls, request, organisation):
        """
            CategoryViewSet for retrieving a list of categories associated with an organisation
        """
        org_name = Organisation.objects.get(organisation_name=organisation)
        queryset = Category.objects.filter(organisation_name=org_name)

        # Serialize and return
        serialized = CategorySerializer(queryset, context={'get': 'retrieve'}, many=True).data

        return Response(serialized)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects
    serializer_class = FileSerializer

    @classmethod
    def list(cls, request):
        """
            FileViewSet for getting a list of output files predicted by the ML model
            for the input data(citizen responses) input by all organisations registered with the application
        """
        queryset = File.objects.all()

        # Serialize and return
        serialized = FileSerializer(queryset, context={'get': 'list'}, many=True).data

        return Response(serialized)

    @classmethod
    def retrieve(cls, request, organisation):
        """
            FileViewSet for retrieving a list of output files predicted by the ML model
            for the input data(citizen responses) input by a specific organisation
        """
        org_name = Organisation.objects.get(organisation_name=organisation)
        queryset = File.objects.filter(organisation_name=org_name).order_by('ckpt_date')

        # Serialize and return
        serialized = FileSerializer(queryset, context={'get': 'retrieve'}, many=True).data

        return Response(serialized)


class ModelCPView(APIView):
    """
    Arguments:  1) APIView: Handles POST requests of type DRF Request instance. 
    Methods:    1) post: This handler is utilized for ICMC App to send json Input to ML API endpoint
    Workflow:   1) On retrieval of DICT containing one or more complaint-category pair, the complaints are separately retrieved
                   to be fed into the method get_top_3_cats_with_prob(complaint_description).
                2) The ClassificationService class handles the request to the ICMC ML model.
                3) The output/ directory is created in order to save the ML model output results based on org_name, ckpt_date.
                4) The input category-complaint pairs are stored (unique pairs) in UserCategory, UserComplaint models required for Input to
                   wordcloud API.
                5) The output from the ICMC ML model is sent to the ICMC application as an HTTPResponse (JSON format).

    """
    def post(self, request):
        ml_input_json_data=json.loads(request.body)
        complaint_description = list(ml_input_json_data.keys())
        model = ClassificationService()
        category_list = model.get_top_3_cats_with_prob(complaint_description)
        
        print("**************The Output is*************************\n\n\n\n\n\n\n")
        print(str(complaint_description) + " : \n" + str(category_list))
        ml_output = []

        for complaint, cat in zip(complaint_description, category_list):
            row_dict = {}
            cat_list = []
            cat_list = list(cat.keys())
            row_dict['complaint'] = complaint
            row_dict['category'] = cat_list
            ml_output.append(row_dict)

        org_name = Organisation.objects.get(organisation_name='ICMC')
        file_instance = File.objects.create(
            organisation_name=org_name,
            has_prediction = True,
        )
        file_instance.save()

        output_directory_path = os.path.join(MEDIA_ROOT, f'{file_instance.organisation_name}/{file_instance.ckpt_date.date()}/output')
        if not os.path.exists(output_directory_path):
            os.makedirs(output_directory_path)

        file_id = str(file_instance.id)
        output_file_json_name = 'ml_output__'+file_id+'.json'
        output_file_json_path = os.path.join(output_directory_path, output_file_json_name)

        with open(output_file_json_path, 'w') as temp:
            json.dump(ml_output, temp)
        file_instance.output_file_json = output_file_json_path
        file_instance.save()

        for category, complaint in zip(list(ml_input_json_data.values()), list(ml_input_json_data.keys())):
            if UserCategory.objects.filter(organisation_name=org_name, user_category=category).exists():
                cat_queryset = UserCategory.objects.filter(organisation_name=org_name)
                for cat in cat_queryset:
                    db_complaint = UserComplaint.objects.get(user_category=cat)
                    str_complaint = str(db_complaint.user_complaint)
                    if (str_complaint.lower()==complaint.lower()):
                        flag = 1
                        break
                    else:
                        flag = 0
                if flag==0:
                    user_category_instance = UserCategory.objects.create(
                        organisation_name=org_name,
                        user_category=category,
                    )
                    user_category_instance.save()
                    user_complaint_instance = UserComplaint.objects.create(
                        user_category=user_category_instance,
                        user_complaint=complaint,
                    )
                    user_complaint_instance.save()
            else:
                user_category_instance = UserCategory.objects.create(
                    organisation_name=org_name,
                    user_category=category,
                )
                user_category_instance.save()
                user_complaint_instance = UserComplaint.objects.create(
                    user_category=user_category_instance,
                    user_complaint=complaint,
                )
                user_complaint_instance.save()
        return HttpResponse(json.dumps(ml_output), content_type="application/json")

schema_view = get_swagger_view(title="Swagger Docs")


class ModelWCView(APIView):
    """
    Arguments:  1) APIView: Requests passed to the handler methods will be REST framework's Request instances
    Methods:    1) get: This handler is utilized by ICMC App to request json wordcloud data generated by the wordcloud model
    Workflow:   1) The input category-complaint pairs are stored (unique pairs) in UserCategory, UserComplaint models required for Input to
                   wordcloud API.
                2) All the complaints along with their categories of the ICMC organisation is fetched from the database
                3) Converting the data from queryset to the required Dictionary format {category:[comp1,comp2],} for generate_wordcloud model.
                4) The output from the WordCloud model is sent to the ICMC application as an HTTPResponse (JSON format).

    """
    def get(self, request):

        org_obj = Organisation.objects.get(organisation_name='ICMC')


        """
        Generates the wordcloud input format: { category: [complaint1, complaint2 ,..], }, which is separated by categories
        """
        # user_category_queryset = UserCategory.objects.filter(
        #     organisation_name=org_obj)
        # wc_input = {}
        # for user_category_queryset_instance in user_category_queryset:

        #     if str(user_category_queryset_instance.user_category) in wc_input.keys():
        #         user_comp_instance = UserComplaint.objects.get(user_category=user_category_queryset_instance)                
        #         wc_input[str(user_category_queryset_instance.user_category)].append(str(user_comp_instance.user_complaint))

        #     else:
        #         l_compaint = []
        #         user_comp_instance = UserComplaint.objects.get(user_category=user_category_queryset_instance)
        #         l_compaint.append(str(user_comp_instance.user_complaint))
        #         wc_input[str(user_category_queryset_instance.user_category)] = l_compaint

        '''
        Format of input fed into the wordcoud is [complaint1, complaint2,]
        Wordcloud output is generated using the complaints created within past 3 months.
        New wordcloud data is generated only if the previous output was generated more than a week ago, else the prev output is returned.
        '''
        wc_input = []

        current_datetime = datetime.now()
        prev_week_datetime = current_datetime - timedelta(days=7)
        three_months_before = current_datetime - timedelta(days=90)
        
        if File.objects.filter(wordcloud_data__icontains = 'wc_output').filter(ckpt_date__gt = prev_week_datetime):
            f = File.objects.filter(wordcloud_data__icontains = 'wc_output').get(ckpt_date__gt = prev_week_datetime)

            temp1 = f.filename
            temp2 = os.path.splitext(temp1)
            custom_input_file_name = temp2[0]
            
            wc_output_json_file_name = custom_input_file_name+'.json'
            results = os.path.join(MEDIA_ROOT, f'{f.organisation_name}/{f.ckpt_date.date()}/wc_output/{wc_output_json_file_name}')

            with open(results, 'r') as content:
                wc_output = json.load(content)

            # print("if got executed")

            # return render(request, './Venter/wordcloud.html', {'words':wc_output})
            return HttpResponse(json.dumps(wc_output), content_type="application/json")

        else:
            # print("else got executed")
            user_category_queryset = UserCategory.objects.filter(
                organisation_name=org_obj).filter(creation_date__gt = three_months_before)
            
            for user_category_queryset_instance in user_category_queryset:
                user_comp_instance = UserComplaint.objects.get(user_category=user_category_queryset_instance)                
                wc_input.append(str(user_comp_instance.user_complaint))
            
            wc_output = generate_wordcloud(wc_input)

            file_instance = File.objects.create(organisation_name = org_obj, ckpt_date = datetime.now())
            file_id = str(file_instance.id)

            output_directory_path = os.path.join(MEDIA_ROOT, f'{file_instance.organisation_name}/{file_instance.ckpt_date.date()}/wc_output')
            if not os.path.exists(output_directory_path):
                os.makedirs(output_directory_path)

            output_file_json_name = 'wc_output__'+file_id+'.json'
            output_file_json_path = os.path.join(output_directory_path, output_file_json_name)

            
            
            with open(output_file_json_path, 'w') as f:
                json.dump(wc_output,f)

            file_instance.wordcloud_data = output_file_json_path
            file_instance.save()
            if File.objects.filter(wordcloud_data__icontains = 'wc_output').exists():
                File.objects.filter(ckpt_date__lt=datetime.now()-timedelta(days=1)).delete()

            return HttpResponse(json.dumps(wc_output), content_type="application/json")

        """
        Below code generates the wordcloud output using the entire database. 
        """
        
        # for user_category_queryset_instance in user_category_queryset:
        #     user_comp_instance = UserComplaint.objects.get(user_category=user_category_queryset_instance)                
        #     wc_input.append(str(user_comp_instance.user_complaint))
        
        # wc_output = generate_wordcloud(wc_input)

        # return HttpResponse(json.dumps(wc_output), content_type="application/json")
