from django.core.files.uploadhandler import FileUploadHandler, StopUpload

from .validators import MAX_UPLOAD_SIZE_BYTES


class DocumentUploadSizeHandler(FileUploadHandler):
    """Interrompe a gravação temporária quando os arquivos passam do limite."""

    def __init__(self, request=None):
        super().__init__(request)
        self.received_size = 0

    def receive_data_chunk(self, raw_data, start):
        self.received_size += len(raw_data)
        if self.received_size > MAX_UPLOAD_SIZE_BYTES:
            self.request.document_upload_too_large = True
            raise StopUpload(connection_reset=False)
        return raw_data

    def file_complete(self, file_size):
        return None
