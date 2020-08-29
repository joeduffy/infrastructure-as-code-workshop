from pulumi import export, StackReference, Output, ResourceOptions
from pulumi_kubernetes import Provider
from pulumi_kubernetes.apps.v1 import Deployment
from pulumi_kubernetes.core.v1 import Service, Namespace
import pulumi

# Create StackReference to the Kubernetes cluster stack
config  = pulumi.Config()
stackRef = config.require("clusterStackRef");
infra = StackReference(f"{stackRef}")

# Declare a provider using the KubeConfig we created
# This will be used to interact with the EKS cluster
kubeconfig = infra.get_output("kubeconfig").apply(lambda c: json.dumps(c))
k8s_provider = Provider("k8s-provider", kubeconfig=kubeconfig)

# Create a Namespace object https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/
ns = Namespace("app-ns",
    metadata={
       "name": "joe-duffy",
    },
    opts=ResourceOptions(provider=k8s_provider)
)

app_labels = {
    "app": "iac-workshop"
}
app_deployment = Deployment("app-dep",
    metadata={
        "namespace": ns.metadata["name"]
    },
    spec={
        "selector": {
            "match_labels": app_labels,
        },
        "replicas": 3,
        "template": {
            "metadata": {
                "labels": app_labels,
            },
            "spec": {
                "containers": [{
                    "name": "iac-workshop",
                    "image": "jocatalin/kubernetes-bootcamp:v2",
                }],
            },
        },
    },
    opts=ResourceOptions(provider=k8s_provider)
)

service = Service("app-service",
    metadata={
      "namespace": ns.metadata["name"],
      "labels": app_labels
    },
    spec={
      "ports": [{
          "port": 80,
          "target_port": 8080,
      }],
      "selector": app_labels,
      "type": "LoadBalancer",
    },
    opts=ResourceOptions(provider=k8s_provider)
)

hostname = service.status['load_balancer']['ingress'][0]['hostname']
port = service.spec['ports'][0]['port'].apply(lambda p: str(int(p)))
export('url', Output.concat("http://", hostname, ":", port))
