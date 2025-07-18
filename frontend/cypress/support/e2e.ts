// ***********************************************************
// This file is processed and loaded automatically before your test files.
// You can change the location of this file or turn off processing support files with the 'supportFile' configuration option.
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Add global type declarations
declare global {
  namespace Cypress {
    interface Chainable {
      login(email?: string, password?: string): Chainable<void>;
      logout(): Chainable<void>;
      uploadFile(fileName: string, fileContent: string, mimeType?: string): Chainable<void>;
      waitForApi(alias: string): Chainable<void>;
      checkAccessibility(): Chainable<void>;
    }
  }
}