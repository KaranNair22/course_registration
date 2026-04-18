from django import forms

from .models import Course, CourseSection


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'title', 'credits', 'dept', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CS101'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'dept': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = [
            'course',
            'term',
            'section_no',
            'instructor',
            'room_text',
            'timeslot_text',
            'capacity',
            'status',
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.Select(attrs={'class': 'form-select'}),
            'section_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'room_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Room 101'}),
            'timeslot_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MWF 10:00-11:00'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

