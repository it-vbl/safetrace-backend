 # myapp/fields.py
from django import forms
from django.contrib.postgres.fields import ArrayField

class ChoiceArrayField(ArrayField):
    """
    A custom ArrayField that renders as a MultipleChoiceField with checkbox widget.
    
    This field extends Django's ArrayField to provide a form field that displays
    multiple choice options as checkboxes, allowing users to select multiple values
    from a predefined list of choices.
    
    Attributes:
        base_field: The base field that contains the choices for the array elements.
    """
    
    def formfield(self, **kwargs):
        defaults = {
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
            "widget": forms.CheckboxSelectMultiple,
            **kwargs
        }
        return super(ArrayField, self).formfield(**defaults)
