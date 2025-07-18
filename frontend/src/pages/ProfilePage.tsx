import React from 'react';
import { Container, Typography, Box, Paper, TextField, Button, Divider } from '@mui/material';
import { useAuth } from '../hooks/useAuth';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <Container maxWidth="md">
      <Box mb={4}>
        <Typography variant="h4">
          Profile Settings
        </Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Account Information
        </Typography>
        <Box component="form" sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Full Name"
            value={user?.full_name || ''}
            margin="normal"
            disabled
          />
          <TextField
            fullWidth
            label="Email"
            value={user?.email || ''}
            margin="normal"
            disabled
          />
          <TextField
            fullWidth
            label="Roles"
            value={user?.roles?.join(', ') || ''}
            margin="normal"
            disabled
          />
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Change Password
        </Typography>
        <Box component="form" sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="Current Password"
            type="password"
            margin="normal"
          />
          <TextField
            fullWidth
            label="New Password"
            type="password"
            margin="normal"
          />
          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            margin="normal"
          />
          <Button
            variant="contained"
            sx={{ mt: 2 }}
            disabled
          >
            Update Password
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default ProfilePage;