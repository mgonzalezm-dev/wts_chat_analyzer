// ***********************************************
// Custom Cypress commands
// ***********************************************
import 'cypress-axe';

// cypress-axe already provides injectAxe and checkA11y commands

// Login command
Cypress.Commands.add('login', (email?: string, password?: string) => {
  const userEmail = email || Cypress.env('testUser').email;
  const userPassword = password || Cypress.env('testUser').password;
  
  cy.visit('/login');
  cy.get('input[name="email"]').type(userEmail);
  cy.get('input[name="password"]').type(userPassword);
  cy.get('button[type="submit"]').click();
  
  // Wait for redirect to dashboard
  cy.url().should('include', '/dashboard');
  cy.get('[data-testid="user-menu"]').should('be.visible');
});

// Logout command
Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

// Upload file command
Cypress.Commands.add('uploadFile', (fileName: string, fileContent: string, mimeType = 'text/plain') => {
  cy.get('input[type="file"]').then(input => {
    const blob = new Blob([fileContent], { type: mimeType });
    const file = new File([blob], fileName, { type: mimeType });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    
    const inputElement = input[0] as HTMLInputElement;
    inputElement.files = dataTransfer.files;
    
    cy.wrap(input).trigger('change', { force: true });
  });
});

// Wait for API command
Cypress.Commands.add('waitForApi', (alias: string) => {
  cy.intercept('GET', `${Cypress.env('apiUrl')}/**`).as(alias);
  cy.wait(`@${alias}`);
});

// Check accessibility command
Cypress.Commands.add('checkAccessibility', () => {
  cy.injectAxe();
  cy.checkA11y();
});

// Export empty object to make this a module
export {};