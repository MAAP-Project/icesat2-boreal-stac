from request_cognito_oauth_token import main
import requests
import pystac
import json
creds = main.get_creds("MAAP-STAC-auth-dev/MAAP-workflows")

item = pystac.read_file('/Users/emiletenezakis/devseed/rio-stac/icesat2-items/items/boreal_agb_202302151676430794_26340.json')

result = requests.post(
    url='https://stac-ingestor.dit.maap-project.org/ingestions',
    headers={"Authorization": f"bearer {creds.access_token}"},
    data=json.dumps(item.to_dict())
)

print(result.content)