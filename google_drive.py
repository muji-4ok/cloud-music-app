from io import BytesIO

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools


class GoogleDrive:
    def __init__(self, scopes="https://www.googleapis.com/auth/drive",
                 token="token.json",
                 credentials="credentials.json"):
        storage = file.Storage(token)
        creds = storage.get()

        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(credentials, scopes)
            creds = tools.run_flow(flow, storage)

        self.service = build("drive", "v3",
                             http=creds.authorize(Http())).files()

    def upload(self, name, path, mime_type, return_fields="name, id"):
        metadata = dict(name=name)
        media = MediaFileUpload(path, mimetype=mime_type)
        file = self.service.create(body=metadata, media_body=media,
                                   fields=return_fields).execute()

        return file

    def download(self, file_id, verbose=False):
        request = self.service.get_media(fileId=file_id)
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()

            if verbose:
                print(f"Download [{file_id}] at "
                      f"{int(status.progress() * 100)}%", end="\r")

        if verbose:
            print(f"Download [{file_id}] at {int(status.progress() * 100)}%")

        return buffer

    def get_data(self, file_id):
        response = self.service.get(fileId=file_id).execute()
        return response

    def list_any(self, query="trashed = false", fields="id, name, parents",
                 spaces="drive"):
        fields = f"nextPageToken, files({fields})"
        page_token = None
        files = []

        while True:
            response = self.service.list(q=query, spaces=spaces, fields=fields,
                                         pageToken=page_token).execute()

            for file in response.get("files", []):
                files.append(file)

            page_token = response.get("nextPageToken", None)

            if page_token is None:
                break

        return files

    def list_files(self, query="trashed = false", fields="id, name, parents",
                   spaces="drive"):
        query += "and mimeType != 'application/vnd.google-apps.folder'"

        return self.list_any(query, fields, spaces)

    def list_folders(self, query="trashed = false", fields="id, name, parents",
                     spaces="drive"):
        query += "and mimeType = 'application/vnd.google-apps.folder'"

        return self.list_any(query, fields, spaces)
