from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ReportFolder, Report, HealthParameter, ResourceLink
from .forms import ReportFolderForm, ReportForm
import google.generativeai as genai
import os
import pdfplumber
from PIL import Image
from django.conf import settings
import PIL
import json
from django.utils import timezone
from django.db.models import Q

genai.configure(api_key="AIzaSyDkG8B4qIVeD50QIErPfgnfL2LBijhgNxg")

@login_required
def folder_list(request):
    folders = ReportFolder.objects.filter(user=request.user)
    return render(request, 'folder_list.html', {'folders': folders})

@login_required
def folder_create(request):
    if request.method == 'POST':
        form = ReportFolderForm(request.POST)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            return redirect('reports:folder_list')
    else:
        form = ReportFolderForm()
    return render(request, 'folder_create.html', {'form': form})

@login_required
def folder_detail(request, folder_id):
    folder = get_object_or_404(ReportFolder, pk=folder_id, user=request.user)
    reports = Report.objects.filter(folder=folder)

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.folder = folder
            report.user = request.user  # Ensure user is associated with report
            report.save()
            return redirect('reports:folder_detail', folder_id=folder_id)
    else:
        form = ReportForm()

    return render(request, 'folder_detail.html', {'folder': folder, 'reports': reports, 'form': form})

@login_required
def report_delete(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    folder_id = report.folder.id
    report.delete()
    return redirect('reports:folder_detail', folder_id=folder_id)

@login_required
def folder_delete(request, folder_id):
    folder = get_object_or_404(ReportFolder, pk=folder_id, user=request.user)
    folder.delete()
    return redirect('reports:folder_list')

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_and_save_parameters(report, analysis_data):
    """Extract and save health parameters from analysis data"""
    if not analysis_data or 'structured_data' not in analysis_data:
        return
    
    phone_number = report.phone_number
    structured_data = analysis_data['structured_data']
    
    # Process each parameter in structured_data
    for param_name, param_value in structured_data.items():
        # Try to convert value to float if it seems numeric
        try:
            # Handle values with units like "120 mg/dL"
            if isinstance(param_value, str) and any(c.isdigit() for c in param_value):
                parts = param_value.split()
                if len(parts) > 1 and any(c.isdigit() for c in parts[0]):
                    value = float(''.join(c for c in parts[0] if c.isdigit() or c == '.'))
                    unit = ' '.join(parts[1:])
                else:
                    # Try to extract just the numeric part
                    value = float(''.join(c for c in param_value if c.isdigit() or c == '.'))
                    unit = None
            else:
                # If it's not a string with units, try direct conversion
                value = float(param_value)
                unit = None
                
            # Use update_or_create instead of create to handle existing entries
            HealthParameter.objects.update_or_create(
                report=report,
                parameter_name=param_name,
                defaults={
                    'phone_number': phone_number,
                    'parameter_value': value,
                    'unit': unit,
                    'recorded_date': report.uploaded_at
                }
            )
        except (ValueError, TypeError):
            # Skip parameters that can't be converted to numbers
            continue

def extract_and_save_links(report, analysis_data):
    """Extract and save resource links from analysis data"""
    if not analysis_data or 'links' not in analysis_data:
        return
    
    phone_number = report.phone_number
    links = analysis_data['links']
    
    for link_data in links:
        if isinstance(link_data, dict) and 'title' in link_data and 'url' in link_data:
            ResourceLink.objects.create(
                phone_number=phone_number,
                title=link_data['title'],
                url=link_data['url'],
                report=report,
                added_date=timezone.now()
            )

@login_required
def report_analysis(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(report.file))
    extracted_text = ""

    # Determine file type and extract text accordingly
    if file_path.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_path)
    elif file_path.endswith((".jpg", ".jpeg", ".png")):
        try:
            image = PIL.Image.open(file_path)
            # Convert RGBA to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                background = PIL.Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content([
                'Extract the text from the image in a structured json format and give me realtime reliable international website links of latest articles related to the extracted text... no need to give the links twice, just give once',
                image
            ])
            extracted_text = response.text if response.text else "No medical information found in the image."
        except PIL.UnidentifiedImageError:
            extracted_text = "Error: Invalid or corrupted image file."
        except Exception as e:
            extracted_text = f"Error processing image: {str(e)}"

    # For both PDF and image cases, send to Gemini API for analysis
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Enhanced prompt to extract numeric values where possible
    prompt = f"""Please analyze this medical report and provide the response in JSON format with the following structure:
    {{
        "extracted_text": "Brief summary of the extracted text",
        "structured_data": {{
            "parameter_name1": "numeric_value1 unit1",
            "parameter_name2": "numeric_value2 unit2",
            ...
        }},
        "summary": "Overall analysis summary",
        "links": [
            {{"title": "Article title 1", "url": "URL 1"}},
            {{"title": "Article title 2", "url": "URL 2"}},
            ...
        ]
    }}
    
    Important: For structured_data, try to include actual numeric values for medical parameters like 
    blood pressure, cholesterol, glucose, hemoglobin, etc. with their units.
    
    Here is the report text to analyze: {extracted_text}
    """
    
    response = model.generate_content([prompt])
    
    # Try to parse the JSON response
    analysis_data = None
    raw_response = response.text
    
    try:
        # Extract JSON if it's wrapped in markdown code blocks
        if "```json" in raw_response and "```" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0].strip()
            analysis_data = json.loads(json_str)
        # Otherwise try to parse the whole response as JSON
        else:
            analysis_data = json.loads(raw_response)
            
        # Save the analysis data to the report
        report.save_analysis_data(analysis_data)
        
        # Extract and save parameters and links
        extract_and_save_parameters(report, analysis_data)
        extract_and_save_links(report, analysis_data)
        
    except json.JSONDecodeError:
        # If JSON parsing fails, keep the raw text
        pass
    
    return render(request, 'report_analysis.html', {
        'report': report,
        'extracted_data': raw_response if not analysis_data else None,
        'analysis_data': analysis_data
    })

@login_required
def user_dashboard(request):
    # Get all reports for the current user
    reports = Report.objects.filter(user=request.user).order_by('-uploaded_at')
    
    if not reports.exists():
        return render(request, 'dashboard.html', {
            'error': 'No reports found',
            'username': request.user.username
        })
    
    # Get all health parameters for the user's reports
    report_ids = reports.values_list('id', flat=True)
    parameters = HealthParameter.objects.filter(report_id__in=report_ids).order_by('parameter_name', 'recorded_date')
    
    # Organize parameters by name
    param_data = {}
    for param in parameters:
        if param.parameter_name not in param_data:
            param_data[param.parameter_name] = {
                'values': [],
                'dates': [],
                'unit': param.unit or ''
            }
        param_data[param.parameter_name]['values'].append(param.parameter_value)
        param_data[param.parameter_name]['dates'].append(param.recorded_date.strftime('%Y-%m-%d'))
    
    # Get latest resource links from user's reports
    resource_links = ResourceLink.objects.filter(
        report_id__in=report_ids
    ).order_by('-added_date')[:10]  # Get the 10 most recent links
    
    context = {
        'username': request.user.username,
        'reports': reports,
        'parameter_data': json.dumps(param_data),
        'resource_links': resource_links,
        'latest_report': reports.first() if reports.exists() else None
    }
    
    return render(request, 'dashboard.html', context)