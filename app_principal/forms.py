from django import forms

class LoginForm(forms.Form):
    nombre_usuario = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)
