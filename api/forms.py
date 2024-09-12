from django import forms

class GenerateForm(forms.Form):
    exename = forms.CharField(label="Name for EXE file", required=True)
    appname = forms.CharField(label="Custom App Name", required=False)
    iconfile = forms.FileField(label="Custom App Icon (in .png format)", required=False)
    serverIP = forms.CharField(label="Host", required=False)
    apiServer = forms.CharField(label="API Server", required=False)
    key = forms.CharField(label="Key", required=False)
    direction = forms.ChoiceField(widget=forms.RadioSelect, choices=[
        ('incoming', 'Incoming Only'),
        ('outgoing', 'Outgoing Only'),
        ('both', 'Bidirectional')
    ], initial='both')
    installation = forms.ChoiceField(label="Allow Installation", choices=[
        ('installationY', 'Yes, allow installation'),
        ('installationN', 'No, do NOT allow installation')
    ], initial='installationY')
    settings = forms.ChoiceField(label="Allow Settings", choices=[
        ('settingsY', 'Yes, allow settings'),
        ('settingsN', 'No, do NOT allow settings')
    ], initial='settingsY')
    permanentPassword = forms.CharField(widget=forms.PasswordInput(), required=False)
    theme = forms.ChoiceField(choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'Follow System')
    ], initial='system')
    themeDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='default')
    runasadmin = forms.ChoiceField(choices=[('false','No'),('true','Yes')], initial='false')