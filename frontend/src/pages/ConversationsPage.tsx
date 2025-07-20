import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Button,
  TextField,
  InputAdornment,
  Chip,
  LinearProgress,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  MoreVert as MoreIcon,
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { fetchConversations, deleteConversation } from '../store/slices/conversationSlice';
import { addNotification } from '../store/slices/uiSlice';
import FileUploadDialog from '../components/conversation/FileUploadDialog';

const ConversationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dispatch = useAppDispatch();
  const { conversations, pagination, isLoading } = useAppSelector(state => state.conversation);
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [search, setSearch] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  useEffect(() => {
    // Check if we should open upload dialog
    if (searchParams.get('action') === 'import') {
      setUploadDialogOpen(true);
    }
  }, [searchParams]);

  useEffect(() => {
    // Fetch conversations
    dispatch(fetchConversations({
      page: page + 1,
      limit: rowsPerPage,
      search: search || undefined,
    }));
  }, [dispatch, page, rowsPerPage, search]);

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, conversationId: string) => {
    setAnchorEl(event.currentTarget);
    setSelectedConversation(conversationId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedConversation(null);
  };

  const handleDelete = async () => {
    if (selectedConversation) {
      try {
        await dispatch(deleteConversation(selectedConversation)).unwrap();
        dispatch(addNotification({
          type: 'success',
          message: 'Conversation deleted successfully',
        }));
      } catch (error) {
        dispatch(addNotification({
          type: 'error',
          message: 'Failed to delete conversation',
        }));
      }
    }
    handleMenuClose();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4">
            Conversations
          </Typography>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialogOpen(true)}
          >
            Import Conversation
          </Button>
        </Box>
        
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search conversations..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {isLoading && <LinearProgress sx={{ mb: 2 }} />}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell align="center">Messages</TableCell>
              <TableCell align="center">Participants</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell>Imported</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {conversations.map((conversation) => (
              <TableRow
                key={conversation.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => navigate(`/conversations/${conversation.id}`)}
              >
                <TableCell>{conversation.title}</TableCell>
                <TableCell align="center">{conversation.message_count.toLocaleString()}</TableCell>
                <TableCell align="center">{conversation.participant_count}</TableCell>
                <TableCell align="center">
                  <Chip
                    label={conversation.status}
                    color={getStatusColor(conversation.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {format(new Date(conversation.imported_at), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMenuOpen(e, conversation.id);
                    }}
                  >
                    <MoreIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {conversations.length === 0 && !isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    No conversations found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        {pagination && (
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={pagination.total}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        )}
      </TableContainer>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          navigate(`/conversations/${selectedConversation}`);
          handleMenuClose();
        }}>
          <ViewIcon sx={{ mr: 1 }} /> View
        </MenuItem>
        <MenuItem onClick={() => {
          // TODO: Implement export
          handleMenuClose();
        }}>
          <DownloadIcon sx={{ mr: 1 }} /> Export
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} /> Delete
        </MenuItem>
      </Menu>

      <FileUploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
      />
    </Container>
  );
};

export default ConversationsPage;