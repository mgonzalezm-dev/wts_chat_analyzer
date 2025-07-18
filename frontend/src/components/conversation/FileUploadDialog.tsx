import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Close as CloseIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useAppDispatch } from '../../hooks/redux';
import { importConversationFile } from '../../store/slices/conversationSlice';
import { addNotification } from '../../store/slices/uiSlice';

interface FileUploadDialogProps {
  open: boolean;
  onClose: () => void;
}

interface UploadFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

const FileUploadDialog: React.FC<FileUploadDialogProps> = ({ open, onClose }) => {
  const dispatch = useAppDispatch();
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      status: 'pending' as const,
      progress: 0,
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/json': ['.json'],
      'application/zip': ['.zip'],
    },
    maxSize: 104857600, // 100MB
  });

  const handleUpload = async () => {
    setIsUploading(true);

    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'pending') continue;

      // Update status to uploading
      setFiles(prev => prev.map((f, idx) => 
        idx === i ? { ...f, status: 'uploading', progress: 50 } : f
      ));

      try {
        await dispatch(importConversationFile(files[i].file)).unwrap();
        
        // Update status to success
        setFiles(prev => prev.map((f, idx) => 
          idx === i ? { ...f, status: 'success', progress: 100 } : f
        ));

        dispatch(addNotification({
          type: 'success',
          message: `Successfully imported ${files[i].file.name}`,
        }));
      } catch (error) {
        // Update status to error
        setFiles(prev => prev.map((f, idx) => 
          idx === i ? { 
            ...f, 
            status: 'error', 
            progress: 0, 
            error: 'Failed to import file' 
          } : f
        ));

        dispatch(addNotification({
          type: 'error',
          message: `Failed to import ${files[i].file.name}`,
        }));
      }
    }

    setIsUploading(false);
  };

  const handleRemoveFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleClose = () => {
    if (!isUploading) {
      setFiles([]);
      onClose();
    }
  };

  const getFileIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <FileIcon />;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Import WhatsApp Conversation
        <IconButton
          aria-label="close"
          onClick={handleClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
          }}
          disabled={isUploading}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent>
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'divider',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
            mb: 2,
          }}
        >
          <input {...getInputProps()} />
          <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            or click to select files
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" mt={1}>
            Supported formats: .txt, .json, .zip (max 100MB)
          </Typography>
        </Box>

        {files.length > 0 && (
          <>
            <Typography variant="subtitle2" gutterBottom>
              Selected Files ({files.length})
            </Typography>
            <List>
              {files.map((uploadFile, index) => (
                <ListItem
                  key={index}
                  secondaryAction={
                    !isUploading && uploadFile.status === 'pending' && (
                      <IconButton edge="end" onClick={() => handleRemoveFile(index)}>
                        <CloseIcon />
                      </IconButton>
                    )
                  }
                >
                  <ListItemIcon>
                    {getFileIcon(uploadFile.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={uploadFile.file.name}
                    secondary={
                      uploadFile.status === 'error' 
                        ? uploadFile.error 
                        : `${(uploadFile.file.size / 1024 / 1024).toFixed(2)} MB`
                    }
                  />
                  {uploadFile.status === 'uploading' && (
                    <Box sx={{ width: '100px', ml: 2 }}>
                      <LinearProgress variant="determinate" value={uploadFile.progress} />
                    </Box>
                  )}
                </ListItem>
              ))}
            </List>
          </>
        )}

        <Alert severity="info" sx={{ mt: 2 }}>
          Your conversation data will be processed securely and will only be accessible to you.
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={isUploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={files.length === 0 || isUploading || files.every(f => f.status !== 'pending')}
          startIcon={<UploadIcon />}
        >
          {isUploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default FileUploadDialog;