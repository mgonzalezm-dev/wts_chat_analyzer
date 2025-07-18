describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should redirect to login when not authenticated', () => {
    cy.url().should('include', '/login');
  });

  it('should allow user registration', () => {
    cy.visit('/login');
    cy.contains('Sign up').click();
    
    // Fill registration form
    cy.get('input[name="email"]').type('newuser@example.com');
    cy.get('input[name="full_name"]').type('New Test User');
    cy.get('input[name="password"]').type('TestPassword123!');
    cy.get('input[name="confirmPassword"]').type('TestPassword123!');
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Should redirect to dashboard after successful registration
    cy.url().should('include', '/dashboard');
    cy.contains('Welcome, New Test User').should('be.visible');
  });

  it('should allow user login', () => {
    cy.visit('/login');
    
    // Fill login form
    cy.get('input[name="email"]').type(Cypress.env('testUser').email);
    cy.get('input[name="password"]').type(Cypress.env('testUser').password);
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard');
    cy.get('[data-testid="user-menu"]').should('be.visible');
  });

  it('should show error on invalid credentials', () => {
    cy.visit('/login');
    
    // Fill with invalid credentials
    cy.get('input[name="email"]').type('invalid@example.com');
    cy.get('input[name="password"]').type('wrongpassword');
    
    // Submit form
    cy.get('button[type="submit"]').click();
    
    // Should show error message
    cy.contains('Invalid email or password').should('be.visible');
    cy.url().should('include', '/login');
  });

  it('should allow user logout', () => {
    // Login first
    cy.login();
    
    // Logout
    cy.get('[data-testid="user-menu"]').click();
    cy.get('[data-testid="logout-button"]').click();
    
    // Should redirect to login
    cy.url().should('include', '/login');
    
    // Try to access protected route
    cy.visit('/dashboard');
    cy.url().should('include', '/login');
  });

  it('should persist authentication on page refresh', () => {
    // Login
    cy.login();
    
    // Refresh page
    cy.reload();
    
    // Should still be logged in
    cy.url().should('include', '/dashboard');
    cy.get('[data-testid="user-menu"]').should('be.visible');
  });

  it('should handle password reset flow', () => {
    cy.visit('/login');
    cy.contains('Forgot password?').click();
    
    // Enter email
    cy.get('input[name="email"]').type('test@example.com');
    cy.get('button[type="submit"]').click();
    
    // Should show success message
    cy.contains('Password reset email sent').should('be.visible');
  });
});