#!/usr/bin/env python3
"""
ssml_to_mp3_google_signed.py
Batch convert SSML files to MP3 using Google Cloud Text-to-Speech,
upload to a private GCS bucket, and create V4 signed URLs using IAM signBlob.
Requires:
  pip install google-cloud-texttospeech google-cloud-storage google-api-python-client google-auth requests
Auth: ADC (Workload Identity in GitHub Actions or gcloud auth application-default login).
"""
import argparse, base64, hashlib, json, os, sys, time, urllib.parse
from datetime import datetime
from google.cloud import texttospeech, storage
import google.auth
from googleapiclient.discovery import build

def _urlencode(value): return urllib.parse.quote(value, safe='')
def iam_sign_blob(service_account_email: str, data: bytes, credentials):
    service = build('iamcredentials', 'v1', credentials=credentials, cache_discovery=False)
    name = f'projects/-/serviceAccounts/{service_account_email}'
    payload_b64 = base64.b64encode(data).decode('utf-8')
    request = service.projects().serviceAccounts().signBlob(name=name, body={'payload': payload_b64})
    resp = request.execute()
    sig_b64 = resp.get('signedBlob')
    if not sig_b64: raise RuntimeError("signBlob returned no signature")
    return base64.b64decode(sig_b64)

def generate_v4_signed_url(bucket_name: str, blob_name: str, service_account_email: str, credentials, expires: int = 3600):
    method = 'GET'
    host = 'storage.googleapis.com'
    canonical_uri = f'/{bucket_name}/{urllib.parse.quote(blob_name, safe="/")}'
    now = datetime.utcnow()
    datestamp = now.strftime('%Y%m%d')
    timestamp = now.strftime('%Y%m%dT%H%M%SZ')
    credential_scope = f'{datestamp}/auto/storage/goog4_request'
    credential = f'{service_account_email}/{credential_scope}'
    query_params = {
        'X-Goog-Algorithm': 'GOOG4-RSA-SHA256',
        'X-Goog-Credential': credential,
        'X-Goog-Date': timestamp,
        'X-Goog-Expires': str(expires),
        'X-Goog-SignedHeaders': 'host'
    }
    canonical_qs = '&'.join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in sorted(query_params.items()))
    canonical_headers = f'host:{host}\n'
    signed_headers = 'host'
    payload_hash = 'UNSIGNED-PAYLOAD'
    canonical_request = '\n'.join([method, canonical_uri, canonical_qs, canonical_headers, signed_headers, payload_hash]).encode('utf-8')
    hashed_cr = hashlib.sha256(canonical_request).hexdigest()
    string_to_sign = '\n'.join(['GOOG4-RSA-SHA256', timestamp, credential_scope, hashed_cr]).encode('utf-8')
    signature_bytes = iam_sign_blob(service_account_email, string_to_sign, credentials)
    signature_hex = signature_bytes.hex()
    final_qs = canonical_qs + '&X-Goog-Signature=' + signature_hex
    url = f'https://{host}{canonical_uri}?{final_qs}'
    return url

def synthesize_ssml(ssml: str, voice: str, language_code: str):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(ssml=ssml)
    voice_params = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    resp = client.synthesize_speech(input=input_text, voice=voice_params, audio_config=audio_config)
    return resp.audio_content

def upload_and_sign(bucket_name: str, blob_name: str, audio_bytes: bytes, service_account_email: str, credentials, signed_url_ttl=3600*24*7):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(audio_bytes, content_type='audio/mpeg')
    url = generate_v4_signed_url(bucket_name, blob_name, service_account_email, credentials, expires=signed_url_ttl)
    return url

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', default='.', help='Directory with SSML files')
    parser.add_argument('--pattern', default='elder_*.ssml', help='Glob pattern for SSML files')
    parser.add_argument('--outdir', default='mp3s', help='Local output dir')
    parser.add_argument('--voice', default='en-US-Wavenet-D')
    parser.add_argument('--lang', default='en-US')
    parser.add_argument('--upload-bucket', required=True)
    parser.add_argument('--gcs-prefix', default='elder-demo')
    parser.add_argument('--parallel', type=int, default=2)
    parser.add_argument('--signed-ttl', type=int, default=3600*24*7)
    parser.add_argument('--webhook', default=None, help='Optional webhook URL to post signed URLs JSON')
    args = parser.parse_args()

    import glob, concurrent.futures
    os.makedirs(args.outdir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(args.input_dir, args.pattern)))
    if not files:
        print("No files found for pattern", args.pattern)
        sys.exit(1)
    creds, project = google.auth.default()
    results = []
    def process_file(fpath):
        try:
            base = os.path.splitext(os.path.basename(fpath))[0]
            outname = f"{base}.mp3"
            print("Processing", fpath)
            with open(fpath, 'r', encoding='utf-8-sig') as fh:
                ssml = fh.read()
            audio = synthesize_ssml(ssml, args.voice, args.lang)
            local_path = os.path.join(args.outdir, outname)
            with open(local_path, 'wb') as fh:
                fh.write(audio)
            blob_name = f"{args.gcs_prefix.rstrip('/')}/{outname}"
            url = upload_and_sign(args.upload_bucket, blob_name, audio, "rossfire-sa@hallowed-pager-471409-g5.iam.gserviceaccount.com", creds, signed_url_ttl=args.signed_ttl)
            print(f"Uploaded and signed: {url}")
            return {'file': fpath, 'mp3': local_path, 'signed_url': url, 'error': None}
        except Exception as e:
            print("Error processing", fpath, e)
            return {'file': fpath, 'mp3': None, 'signed_url': None, 'error': str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as ex:
        futures = [ex.submit(process_file, f) for f in files]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())
    if args.webhook:
        import requests
        payload = {'results': [{'file': r['file'], 'signed_url': r['signed_url'], 'error': r['error']} for r in results]}
        try:
            resp = requests.post(args.webhook, json=payload, timeout=30)
            print("Webhook posted, status:", resp.status_code)
        except Exception as e:
            print("Webhook post failed:", e)
    print(json.dumps(results, indent=2))
if __name__ == '__main__':
    main()
