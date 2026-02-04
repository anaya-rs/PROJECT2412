import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, FileText, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UploadedFile } from '@/types/lesson';

interface FileUploadProps {
  file: UploadedFile | null;
  onFileUpload: (file: UploadedFile) => void;
  onFileRemove: () => void;
  error?: string;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_TYPES = {
  'text/plain': ['.txt'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/msword': ['.doc'],
};

export function FileUpload({ file, onFileUpload, onFileRemove, error }: FileUploadProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const uploadedFile = acceptedFiles[0];
      if (!uploadedFile) return;

      const reader = new FileReader();
      reader.onload = () => {
        const content = reader.result as string;
        const wordCount = content.split(/\s+/).filter(Boolean).length;
        
        onFileUpload({
          name: uploadedFile.name,
          size: uploadedFile.size,
          type: uploadedFile.type,
          content,
          wordCount,
          characterCount: content.length,
        });
      };
      reader.readAsText(uploadedFile);
    },
    [onFileUpload]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxSize: MAX_FILE_SIZE,
    maxFiles: 1,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (file) {
    return (
      <div className="border-2 border-border rounded-lg p-6 bg-card animate-fade-in">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-primary-light rounded-lg flex items-center justify-center flex-shrink-0">
            <FileText className="w-6 h-6 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-foreground truncate">{file.name}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {formatFileSize(file.size)}
            </p>
            <div className="flex gap-4 mt-3 text-sm">
              <span className="px-2.5 py-1 bg-muted rounded-md text-muted-foreground">
                {file.wordCount.toLocaleString()} words
              </span>
              <span className="px-2.5 py-1 bg-muted rounded-md text-muted-foreground">
                {file.characterCount.toLocaleString()} characters
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onFileRemove}
            className="text-muted-foreground hover:text-destructive"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragActive 
            ? 'border-primary bg-primary-light' 
            : 'border-border hover:border-primary/50 hover:bg-muted/50'
          }
          ${error ? 'border-destructive' : ''}
        `}
      >
        <input {...getInputProps()} />
        <div className="w-14 h-14 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
          <Upload className={`w-6 h-6 ${isDragActive ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        <p className="text-foreground font-medium mb-1">
          {isDragActive ? 'Drop your file here' : 'Drag & drop your document'}
        </p>
        <p className="text-muted-foreground text-sm mb-4">
          or click to browse files
        </p>
        <p className="text-muted-foreground text-xs">
          Supports TXT, PDF, DOCX • Max 10MB
        </p>
      </div>

      {(error || fileRejections.length > 0) && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>
            {error || fileRejections[0]?.errors[0]?.message || 'Invalid file'}
          </span>
        </div>
      )}
    </div>
  );
}
