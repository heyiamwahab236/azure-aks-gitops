"""Regenerate application-only Helm templates from reviewed local manifests."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
chart = root / 'helm/order-platform'
(chart / 'files').mkdir(exist_ok=True)
documents = []
for name in ['order', 'inventory', 'payment', 'notification', 'frontend']:
    for path in sorted((root / f'k8s/{name}').glob('*.yaml')):
        obj = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
        obj['metadata'].pop('namespace', None)
        if obj['kind'] == 'ConfigMap':
            (chart / 'files/nginx.conf').write_text(obj['data']['default.conf'])
            documents.append('apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: frontend-nginx-config\ndata:\n  default.conf: |\n{{ .Files.Get "files/nginx.conf" | indent 4 }}\n')
            continue
        if obj['kind'] == 'Deployment' and name == 'frontend':
            obj['spec']['template']['metadata'].setdefault('annotations', {})['checksum/frontend-config'] = '{{ .Files.Get "files/nginx.conf" | sha256sum }}'
        content = yaml.safe_dump(obj, sort_keys=False)
        if obj['kind'] == 'Deployment':
            image = obj['spec']['template']['spec']['containers'][0]['image']
            content = content.replace(image, '{{ .Values.images.' + name + ' }}:{{ .Values.imageTag }}')
            content = content.replace('replicas: 1', 'replicas: {{ .Values.replicas }}')
            content = content.replace('order-platform.svc.cluster.local.', '{{ .Release.Namespace }}.svc.cluster.local.')
        documents.append(content)
(chart / 'templates/application.yaml').write_text('\n---\n'.join(documents))
