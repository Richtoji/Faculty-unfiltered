from django.db import models
from django.core.exceptions import ValidationError
import re

BAD_WORDS = ['stupid', 'idiot', 'dumb', 'hate', 'badword', 'abuse']

class Feedback(models.Model):
    CATEGORY_CHOICES = [
        ('Faculty', 'Faculty'),
        ('Subject', 'Subject'),
        ('Infrastructure', 'Infrastructure'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    target = models.CharField(max_length=200, help_text="Teacher's name, Subject name, or facility")
    message = models.TextField()
    document = models.CharField(max_length=255, blank=True, null=True, help_text="Path to uploaded PDF")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True, help_text="Faculty reviews stay False until admin approves.")

    def clean(self):
        super().clean()
        if self.message:
            words = re.findall(r'\b\w+\b', self.message.lower())
            for bw in BAD_WORDS:
                if bw in words:
                    raise ValidationError("Inappropriate language detected. Please be constructive and respectful.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} - {self.target} ({self.rating}/5)"


class Issue(models.Model):
    CATEGORY_CHOICES = [
        ('Electrical', 'Electrical'),
        ('Plumbing', 'Plumbing'),
        ('IT', 'IT'),
        ('Infrastructure', 'Infrastructure'),
        ('Cleanliness', 'Cleanliness'),
        ('Other', 'Other')
    ]
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High')
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved')
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    location = models.CharField(max_length=150)
    description = models.TextField()
    image = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Suggestion(models.Model):
    CATEGORY_CHOICES = [
        ('Academic', 'Academic'),
        ('Infrastructure', 'Infrastructure'),
        ('Events', 'Events'),
        ('Other', 'Other')
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    upvotes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class CampusPhoto(models.Model):
    CATEGORY_CHOICES = [
        ('Events', 'Events'),
        ('Nature', 'Nature'),
        ('Friends', 'Friends'),
        ('Campus Life', 'Campus Life'),
        ('Other', 'Other')
    ]

    image = models.TextField()
    caption = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Campus Life')
    uploader_pseudonym = models.CharField(max_length=100, default='Anonymous Scholar')
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.uploader_pseudonym}'s Photo ({self.id})"

class PhotoComment(models.Model):
    photo = models.ForeignKey(CampusPhoto, on_delete=models.CASCADE, related_name='comments')
    commenter_pseudonym = models.CharField(max_length=100, default='Anonymous')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.commenter_pseudonym} on {self.photo.id}"

class PhotoLike(models.Model):
    photo = models.ForeignKey(CampusPhoto, on_delete=models.CASCADE, related_name='photo_likes')
    user_pseudonym = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('photo', 'user_pseudonym')

    def __str__(self):
        return f"{self.user_pseudonym} liked {self.photo.id}"

class PendingFeedback(Feedback):
    class Meta:
        proxy = True
        verbose_name = "Approval Request"
        verbose_name_plural = "Approval Requests"
