# Project Onboarding Action

Manually onboarding projects can be time-consuming and error-prone. Therefore, it's recommended to use vRealize Automation to automate itself for project creation and 
onboarding. This simple action does the following:

1) Create the project
2) Add all available Cloud Zones to the project. In a real-life situation, you'd probably filter the Cloud Zones to be added based on a property.
3) Share a default "production templates" content source with the project.
4) If so desired, creates a content source and shares it with existing projects.

This action is intended as a template and an inspiration and should not be used as-is!

The bundle.zip file can be imported directly into vRealize Automation For reference, the Python code for the action is published as well.
