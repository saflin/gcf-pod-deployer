from flask import escape
import google.auth
import googleapiclient.discovery
from kubernetes import client
import base64


def hello_http(request):
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'name' in request_json:
        name = request_json['name']
    elif request_args and 'name' in request_args:
        name = request_args['name']
    else:
        name = 'World'

    #list pods from GKE cluster
    list_pods()

    return 'Hello {}!'.format(escape(name))


def get_credentials():
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform',])
    credentials.refresh(google.auth.transport.requests.Request())
    return credentials


def get_cluster_info(credentials):
    gke = googleapiclient.discovery.build('container', 'v1', credentials=credentials,cache_discovery=False)
    name = 'projects/saflin-project/locations/europe-west2/clusters/saflin-gke-cluster'
    gke_clusters = gke.projects().locations().clusters()
    gke_cluster = gke_clusters.get(name=name).execute()
    return gke_cluster


def build_kube_config(gke_cluster, credentials):
    kube_config = client.Configuration()
    kube_config.host = 'https://{}'.format(gke_cluster['endpoint'])
    kube_config.verify_ssl = True
    kube_config.api_key['authorization'] = credentials.token
    kube_config.api_key_prefix['authorization'] = 'Bearer'
    kube_config.ssl_ca_cert = '/tmp/ssl_ca_cert'

    with open(kube_config.ssl_ca_cert, 'wb') as f:
        f.write(base64.decodebytes(gke_cluster['masterAuth']['clusterCaCertificate'].encode()))

    return kube_config


def list_pods():
    credentials = get_credentials()
    gke_cluster = get_cluster_info(credentials)
    kube_config = build_kube_config(gke_cluster, credentials)
    kube_client = client.ApiClient(configuration=kube_config)
    kube_v1 = client.CoreV1Api(kube_client)
    print(kube_v1.list_pod_for_all_namespaces())
