import requests
import uuid
import time

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

bp_content = """
formatVersion: 1
inputs: {}
resources:
  Cloud_Machine_1:
    type: Cloud.Machine
    properties:
      image: ubuntu-18
      flavor: tiny
"""

url_root = 'https://cava-r-90-132.eng.vmware.com'

def get(url):
    r = requests.get(url_root + url, headers=headers, verify=False)
    if r.status_code < 200 or r.status_code > 299:
        raise Exception('HTTP error %d: %s' % (r.status_code, r.content))
    return r.json()

def delete(url):
    r = requests.delete(url_root + url, headers=headers, verify=False)
    if r.status_code < 200 or r.status_code > 299:
        raise Exception('HTTP error %d: %s' % (r.status_code, r.content))

def post(url, content):
    r = requests.post(url_root + url, headers=headers, verify=False, json=content)
    if r.status_code < 200 or r.status_code > 299:
        raise Exception('HTTP error %d: %s' % (r.status_code, r.content))
    return r.json()


def handler(context, inputs):
    payload = {
        'refreshToken': context.getSecret(inputs['apiKey'])
    }
    response = post('/iaas/api/login', payload)
    headers['Authorization'] = 'Bearer ' + response['token']
    projectName = inputs['projectName']

    # Collect cloud zones
    if str(inputs.get('addZones', 'False')).lower() == 'true':
        zones = get('/iaas/api/zones')['content']
    else:
        zones = []

    # Create project
    proj = {
        'name': projectName,
        'zoneAssignmentConfigurations':  list(map(lambda z: { 'zoneId': z['id']}, zones))
    }
    proj = post('/iaas/api/projects', proj)
    
    # Make sure we have access to the global template sharing projects
    entitlement = {
        'projectId': proj['id'],
        'definition': {
            'type': 'CatalogSourceIdentifier',
            'id': inputs['globalSourceId'],
            'sourceType': 'com.vmw.blueprint'
        }
    }
    post('/catalog/api/admin/entitlements', entitlement)

    # Automatically share templates with other projects? Create a content source and share it!
    if str(inputs.get('shareTemplates', 'False')).lower() == 'true':
        # We can't add entitlements unless we have at least one catalog item.
        # Create a temporary one that we'll delete later.
        bp = {
            'content': bp_content,
            'name': 'tmp-' + str(uuid.uuid4()),
            'projectId': proj['id'],
            'requestScopeOrg': True
        }
        bp = post('/blueprint/api/blueprints', bp)
        v = {
            'version': '1',
            'release': True
        }
        post('/blueprint/api/blueprints/%s/versions' % bp['id'], v)
    
        # Create a content source for this project. The template we just created will be imported automatically.
        source = {
            'name': projectName + ' Templates',
            'typeId': 'com.vmw.blueprint',
            'config': {
                'sourceProjectId': proj['id']
            }
        }
        source = post('/catalog/api/admin/sources', source)
        while source['itemsImported'] == 0:
            print('Waiting for items to get imported...')
            time.sleep(5)
            source = get('/catalog/api/admin/sources/' + source['id'])
    
        # Add entitlements for this source to all other projects
        for p in get('/iaas/api/projects')["content"]:
            entitlement = {
                'projectId': p['id'],
                'definition': {
                    'type': 'CatalogSourceIdentifier',
                    'id': source['id'],
                    'sourceType': 'com.vmw.blueprint'
                }
            }
            post('/catalog/api/admin/entitlements', entitlement)
            print('Added entitlements for project: ' + p['name'])
    
        # Delete the temporary catalog item
        delete('/blueprint/api/blueprints/' + bp['id'])
    
        # Save the content source again. This forces a re-import of the catalog items
        source = post('/catalog/api/admin/sources', source)



