import React, { useState, useEffect } from 'react';
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
  Button,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Card,
  CardContent,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as ActiveIcon,
  Cancel as InactiveIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  conversation_count?: number;
  storage_used_mb?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const AdminPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    roles: ['user'],
    is_active: true,
  });

  // Load users
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      // const response = await userService.getUsers();
      
      // Mock data
      const mockUsers: User[] = [
        {
          id: '1',
          email: 'admin@example.com',
          full_name: 'Admin User',
          roles: ['admin'],
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          last_login: '2024-01-15T10:00:00Z',
          conversation_count: 0,
          storage_used_mb: 0,
        },
        {
          id: '2',
          email: 'john.doe@example.com',
          full_name: 'John Doe',
          roles: ['user'],
          is_active: true,
          created_at: '2024-01-05T00:00:00Z',
          last_login: '2024-01-15T09:30:00Z',
          conversation_count: 5,
          storage_used_mb: 125.5,
        },
        {
          id: '3',
          email: 'jane.smith@example.com',
          full_name: 'Jane Smith',
          roles: ['user'],
          is_active: true,
          created_at: '2024-01-10T00:00:00Z',
          last_login: '2024-01-14T15:45:00Z',
          conversation_count: 3,
          storage_used_mb: 87.2,
        },
        {
          id: '4',
          email: 'inactive.user@example.com',
          full_name: 'Inactive User',
          roles: ['user'],
          is_active: false,
          created_at: '2023-12-01T00:00:00Z',
          last_login: null,
          conversation_count: 0,
          storage_used_mb: 0,
        },
      ];
      
      setUsers(mockUsers);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = () => {
    setIsCreating(true);
    setSelectedUser(null);
    setFormData({
      email: '',
      full_name: '',
      password: '',
      roles: ['user'],
      is_active: true,
    });
    setUserDialogOpen(true);
  };

  const handleEditUser = (user: User) => {
    setIsCreating(false);
    setSelectedUser(user);
    setFormData({
      email: user.email,
      full_name: user.full_name,
      password: '',
      roles: user.roles,
      is_active: user.is_active,
    });
    setUserDialogOpen(true);
  };

  const handleDeleteUser = (user: User) => {
    setSelectedUser(user);
    setDeleteDialogOpen(true);
  };

  const handleSaveUser = async () => {
    try {
      if (isCreating) {
        // TODO: Create user API call
        console.log('Creating user:', formData);
      } else {
        // TODO: Update user API call
        console.log('Updating user:', selectedUser?.id, formData);
      }
      
      setUserDialogOpen(false);
      loadUsers();
    } catch (error) {
      console.error('Failed to save user:', error);
    }
  };

  const handleConfirmDelete = async () => {
    try {
      // TODO: Delete user API call
      console.log('Deleting user:', selectedUser?.id);
      
      setDeleteDialogOpen(false);
      loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
  };

  const handleToggleUserStatus = async (user: User) => {
    try {
      // TODO: Toggle user status API call
      console.log('Toggling user status:', user.id, !user.is_active);
      loadUsers();
    } catch (error) {
      console.error('Failed to toggle user status:', error);
    }
  };

  const filteredUsers = users.filter(user =>
    user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'moderator':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Admin Panel
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage users, view system statistics, and configure settings
        </Typography>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab icon={<SecurityIcon />} label="Users" />
          <Tab icon={<HistoryIcon />} label="Audit Logs" />
          <Tab icon={<SettingsIcon />} label="Settings" />
        </Tabs>
      </Paper>

      {/* Users Tab */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          {/* Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <TextField
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
              sx={{ width: 300 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<RefreshIcon />}
                onClick={loadUsers}
                variant="outlined"
              >
                Refresh
              </Button>
              <Button
                startIcon={<AddIcon />}
                onClick={handleCreateUser}
                variant="contained"
              >
                Add User
              </Button>
            </Box>
          </Box>

          {/* Users Table */}
          {loading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>User</TableCell>
                      <TableCell>Roles</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Conversations</TableCell>
                      <TableCell>Storage</TableCell>
                      <TableCell>Last Login</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {filteredUsers
                      .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                      .map((user) => (
                        <TableRow key={user.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2">{user.full_name}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {user.email}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {user.roles.map((role) => (
                                <Chip
                                  key={role}
                                  label={role}
                                  size="small"
                                  color={getRoleColor(role)}
                                />
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              icon={user.is_active ? <ActiveIcon /> : <InactiveIcon />}
                              label={user.is_active ? 'Active' : 'Inactive'}
                              color={user.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>{user.conversation_count || 0}</TableCell>
                          <TableCell>{user.storage_used_mb?.toFixed(1) || 0} MB</TableCell>
                          <TableCell>
                            {user.last_login
                              ? format(new Date(user.last_login), 'MMM d, yyyy HH:mm')
                              : 'Never'}
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              <IconButton
                                size="small"
                                onClick={() => handleEditUser(user)}
                                title="Edit user"
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleToggleUserStatus(user)}
                                title={user.is_active ? 'Deactivate user' : 'Activate user'}
                              >
                                <BlockIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteUser(user)}
                                title="Delete user"
                                disabled={user.roles.includes('admin')}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <TablePagination
                rowsPerPageOptions={[5, 10, 25]}
                component="div"
                count={filteredUsers.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(e, newPage) => setPage(newPage)}
                onRowsPerPageChange={(e) => {
                  setRowsPerPage(parseInt(e.target.value, 10));
                  setPage(0);
                }}
              />
            </>
          )}
        </Paper>

        {/* System Stats */}
        <Box
          sx={{
            mt: 3,
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(4, 1fr)',
            },
            gap: 3,
          }}
        >
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Users
              </Typography>
              <Typography variant="h4">{users.length}</Typography>
              <Typography variant="body2" color="textSecondary">
                {users.filter(u => u.is_active).length} active
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Conversations
              </Typography>
              <Typography variant="h4">
                {users.reduce((sum, u) => sum + (u.conversation_count || 0), 0)}
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Storage
              </Typography>
              <Typography variant="h4">
                {(users.reduce((sum, u) => sum + (u.storage_used_mb || 0), 0) / 1024).toFixed(1)} GB
              </Typography>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Admin Users
              </Typography>
              <Typography variant="h4">
                {users.filter(u => u.roles.includes('admin')).length}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </TabPanel>

      {/* Audit Logs Tab */}
      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Alert severity="info">
            Audit log viewer coming soon. This will show all user actions and system events.
          </Alert>
        </Paper>
      </TabPanel>

      {/* Settings Tab */}
      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Alert severity="info">
            System settings coming soon. Configure storage limits, API keys, and more.
          </Alert>
        </Paper>
      </TabPanel>

      {/* User Dialog */}
      <Dialog open={userDialogOpen} onClose={() => setUserDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{isCreating ? 'Create New User' : 'Edit User'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Full Name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              fullWidth
              required
            />
            {isCreating && (
              <TextField
                label="Password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                fullWidth
                required
              />
            )}
            <FormControl fullWidth>
              <InputLabel>Roles</InputLabel>
              <Select
                multiple
                value={formData.roles}
                onChange={(e) => setFormData({ ...formData, roles: e.target.value as string[] })}
                label="Roles"
              >
                <MenuItem value="user">User</MenuItem>
                <MenuItem value="moderator">Moderator</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">
            {isCreating ? 'Create' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user "{selectedUser?.full_name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminPage;