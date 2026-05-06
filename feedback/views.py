from django.shortcuts import render, redirect
from django.db.models import Avg, Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import ValidationError
import base64
from io import BytesIO
from PIL import Image
from .models import Feedback, Issue, Suggestion, CampusPhoto, PhotoComment, PhotoLike

def process_image(uploaded_file):
    try:
        img = Image.open(uploaded_file)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((1024, 1024))
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded_string}"
    except Exception:
        uploaded_file.seek(0)
        encoded_string = base64.b64encode(uploaded_file.read()).decode('utf-8')
        return f"data:{uploaded_file.content_type};base64,{encoded_string}"

def landing(request):
    return render(request, 'feedback/landing.html')

def login_page(request):
    return render(request, 'feedback/login.html')

def home(request):
    feedback_list = Feedback.objects.filter(is_approved=True)

    # Search by target or message
    search_query = request.GET.get('search', '')
    if search_query:
        feedback_list = feedback_list.filter(
            Q(target__icontains=search_query) | 
            Q(message__icontains=search_query)
        )

    # Filter by category
    category_filter = request.GET.get('category', '')
    if category_filter:
        feedback_list = feedback_list.filter(category=category_filter)

    # Sort
    sort_by = request.GET.get('sort', 'latest')
    if sort_by == 'highest':
        feedback_list = feedback_list.order_by('-rating', '-created_at')
    else:
        feedback_list = feedback_list.order_by('-created_at')

    # Aggregates
    avg_rating = Feedback.objects.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None

    # Pagination
    paginator = Paginator(feedback_list, 6) # Show 6 feedbacks per page.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    cat_list = [{'name': c[0], 'is_selected': c[0] == category_filter} for c in Feedback.CATEGORY_CHOICES]
    sort_list = [
        {'value': 'latest', 'label': 'Latest First', 'is_selected': sort_by == 'latest'},
        {'value': 'highest', 'label': 'Highest Rated', 'is_selected': sort_by == 'highest'}
    ]

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'avg_rating': avg_rating,
        'categories': cat_list,
        'sort_options': sort_list,
    }
    return render(request, 'feedback/home.html', context)

def submit_feedback(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        target = request.POST.get('target')
        message = request.POST.get('message')
        rating = request.POST.get('rating')

        is_approved = False # All reviews now require admin moderation

        feedback = Feedback(category=category, target=target, message=message, rating=rating, is_approved=is_approved)
        
        if 'pdf_file' in request.FILES:
            from django.conf import settings
            from django.core.files.storage import FileSystemStorage
            import os
            
            pdf = request.FILES['pdf_file']
            upload_dir = settings.BASE_DIR / 'uploads'
            os.makedirs(upload_dir, exist_ok=True)
            
            fs = FileSystemStorage(location=upload_dir)
            filename = fs.save(pdf.name, pdf)
            feedback.document = f"/uploads/{filename}"

        try:
            feedback.full_clean()
            feedback.save()
            messages.success(request, 'Review submitted successfully. Awaiting administrative clearance.')
            return redirect('home')
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
    
    cat_list = [c[0] for c in Feedback.CATEGORY_CHOICES]
    rating_list = [{'val': str(i), 'is_selected': i == 5} for i in [5, 4, 3, 2, 1]]
    return render(request, 'feedback/submit.html', {'categories': cat_list, 'rating_options': rating_list})

def issues_view(request):
    issues = Issue.objects.all().order_by('-created_at')
    suggestions = Suggestion.objects.all().order_by('-upvotes', '-created_at')
    
    # Global search for both issues and suggestions
    q = request.GET.get('q', '')
    if q:
        issues = issues.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))
        suggestions = suggestions.filter(Q(title__icontains=q) | Q(description__icontains=q))

    issue_categories = [c[0] for c in Issue.CATEGORY_CHOICES]
    sug_categories = [c[0] for c in Suggestion.CATEGORY_CHOICES]

    context = {
        'issues': issues,
        'suggestions': suggestions,
        'issue_categories': issue_categories,
        'sug_categories': sug_categories,
        'search_query': q
    }
    return render(request, 'feedback/issues.html', context)

def submit_issue(request):
    if request.method == 'POST':
        try:
            issue = Issue(
                title=request.POST.get('title'),
                category=request.POST.get('category'),
                location=request.POST.get('location'),
                description=request.POST.get('description'),
                priority=request.POST.get('priority', 'Medium')
            )
            if 'image' in request.FILES:
                issue.image = process_image(request.FILES['image'])
            issue.full_clean()
            issue.save()
            messages.success(request, 'Issue reported successfully!')
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
        except Exception as e:
            messages.error(request, f"System error during upload: {str(e)}")
    return redirect('issues')

def submit_suggestion(request):
    if request.method == 'POST':
        try:
            sug = Suggestion(
                title=request.POST.get('title'),
                category=request.POST.get('category'),
                description=request.POST.get('description')
            )
            sug.full_clean()
            sug.save()
            messages.success(request, 'Suggestion submitted successfully!')
        except ValidationError as e:
            for err in e.messages:
                messages.error(request, err)
    return redirect('issues')

def upvote_suggestion(request, suggestion_id):
    if request.method == 'POST':
        try:
            sug = Suggestion.objects.get(id=suggestion_id)
            sug.upvotes += 1
            sug.save()
            messages.success(request, 'Upvoted!')
        except Suggestion.DoesNotExist:
            pass
    return redirect('issues')

def gallery_view(request):
    photos = CampusPhoto.objects.all().order_by('-created_at')
    
    cat_filter = request.GET.get('category', '')
    if cat_filter:
        photos = photos.filter(category=cat_filter)
        
    sort_by = request.GET.get('sort', 'latest')
    if sort_by == 'trending':
        photos = photos.order_by('-likes', '-created_at')
        
    categories = [{'name': c[0], 'is_selected': c[0] == cat_filter} for c in CampusPhoto.CATEGORY_CHOICES]
    
    sort_options = [
        {'value': 'latest', 'label': 'Recent Acquisitions', 'is_selected': sort_by == 'latest'},
        {'value': 'trending', 'label': 'Most Admired (Trending)', 'is_selected': sort_by == 'trending'}
    ]
    
    return render(request, 'feedback/gallery.html', {
        'photos': photos,
        'categories': categories,
        'sort_options': sort_options,
        'cat_filter': cat_filter,
        'sort_by': sort_by,
    })

def upload_photo(request):
    if request.method == 'POST':
        if 'image' in request.FILES:
            try:
                photo = CampusPhoto(
                    image=process_image(request.FILES['image']),
                    caption=request.POST.get('caption', ''),
                    category=request.POST.get('category', 'Campus Life'),
                    uploader_pseudonym=request.POST.get('pseudonym', 'Anonymous Scholar')
                )
                photo.full_clean()
                photo.save()
                messages.success(request, 'Photo completely secured into the gallery.')
            except ValidationError as e:
                for err in e.messages:
                    messages.error(request, err)
            except Exception as e:
                messages.error(request, f"System error during photo upload: {str(e)}")
        else:
            messages.error(request, 'Please provide an image.')
    return redirect('gallery')

def like_photo(request, photo_id):
    if request.method == 'POST':
        pseudonym = request.POST.get('pseudonym')
        if not pseudonym:
            messages.error(request, 'Identify yourself to provide appreciation.')
            return redirect('gallery')
            
        try:
            photo = CampusPhoto.objects.get(id=photo_id)
            # Check if this user already liked the photo
            if PhotoLike.objects.filter(photo=photo, user_pseudonym=pseudonym).exists():
                messages.warning(request, 'Your appreciation is already recorded.')
            else:
                PhotoLike.objects.create(photo=photo, user_pseudonym=pseudonym)
                photo.likes += 1
                photo.save()
                messages.success(request, 'Photo appreciated successfully.')
        except CampusPhoto.DoesNotExist:
            pass
    return redirect('gallery')

def add_comment(request, photo_id):
    if request.method == 'POST':
        try:
            photo = CampusPhoto.objects.get(id=photo_id)
            commenter = request.POST.get('pseudonym', 'Anonymous')
            text = request.POST.get('text', '')
            if text:
                comment = PhotoComment(photo=photo, commenter_pseudonym=commenter, text=text)
                comment.full_clean()
                comment.save()
                messages.success(request, 'Comment etched into the record.')
        except (CampusPhoto.DoesNotExist, ValidationError):
            messages.error(request, 'Could not post comment.')
    return redirect('gallery')
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_dashboard(request):
    pending_feedbacks = Feedback.objects.filter(is_approved=False).order_by('-created_at')
    issues = Issue.objects.all().order_by('-created_at')
    
    context = {
        'pending_feedbacks': pending_feedbacks,
        'issues': issues,
    }
    return render(request, 'feedback/admin_dashboard.html', context)

@staff_member_required
def approve_feedback(request, feedback_id):
    if request.method == 'POST':
        try:
            fb = Feedback.objects.get(id=feedback_id)
            fb.is_approved = True
            fb.save()
            messages.success(request, f"Feedback for {fb.target} approved.")
        except Feedback.DoesNotExist:
            messages.error(request, "Feedback not found.")
    return redirect('admin_dashboard')

@staff_member_required
def delete_feedback(request, feedback_id):
    if request.method == 'POST':
        try:
            fb = Feedback.objects.get(id=feedback_id)
            fb.delete()
            messages.success(request, "Feedback deleted.")
        except Feedback.DoesNotExist:
            messages.error(request, "Feedback not found.")
    return redirect('admin_dashboard')

@staff_member_required
def update_issue_status(request, issue_id):
    if request.method == 'POST':
        try:
            issue = Issue.objects.get(id=issue_id)
            new_status = request.POST.get('status')
            if new_status in [s[0] for s in Issue.STATUS_CHOICES]:
                issue.status = new_status
                issue.save()
                messages.success(request, f"Issue '{issue.title}' updated to {new_status}.")
        except Issue.DoesNotExist:
            messages.error(request, "Issue not found.")
    return redirect('admin_dashboard')
