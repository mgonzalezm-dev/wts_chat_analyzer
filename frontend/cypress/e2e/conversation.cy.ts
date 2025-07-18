describe('Conversation Workflow', () => {
  beforeEach(() => {
    // Login before each test
    cy.login();
    cy.visit('/conversations');
  });

  it('should display conversation list', () => {
    // Should show conversations page
    cy.contains('Conversations').should('be.visible');
    cy.get('[data-testid="conversation-list"]').should('exist');
  });

  it('should upload a new conversation', () => {
    // Click upload button
    cy.get('[data-testid="upload-button"]').click();
    
    // Upload dialog should appear
    cy.contains('Upload WhatsApp Chat').should('be.visible');
    
    // Create sample chat content
    const chatContent = `[1/1/24, 10:00 AM] Alice: Hello Bob!
[1/1/24, 10:01 AM] Bob: Hi Alice! How are you?
[1/1/24, 10:02 AM] Alice: I'm doing great, thanks!
[1/1/24, 10:03 AM] Bob: That's wonderful to hear!`;
    
    // Upload file
    cy.uploadFile('test-chat.txt', chatContent);
    
    // Submit upload
    cy.get('[data-testid="upload-submit"]').click();
    
    // Should show success message
    cy.contains('Upload successful').should('be.visible');
    
    // New conversation should appear in list
    cy.get('[data-testid="conversation-list"]').contains('test-chat.txt').should('be.visible');
  });

  it('should view conversation details', () => {
    // Click on first conversation
    cy.get('[data-testid="conversation-item"]').first().click();
    
    // Should navigate to detail page
    cy.url().should('include', '/conversations/');
    
    // Should show message timeline
    cy.get('[data-testid="message-timeline"]').should('be.visible');
    
    // Should show conversation info
    cy.get('[data-testid="conversation-info"]').should('be.visible');
  });

  it('should search messages in conversation', () => {
    // Navigate to a conversation
    cy.get('[data-testid="conversation-item"]').first().click();
    
    // Enter search query
    cy.get('[data-testid="message-search"]').type('hello');
    
    // Should highlight matching messages
    cy.get('[data-testid="message-item"].highlighted').should('exist');
    
    // Clear search
    cy.get('[data-testid="clear-search"]').click();
    cy.get('[data-testid="message-item"].highlighted').should('not.exist');
  });

  it('should filter messages by participant', () => {
    // Navigate to a conversation
    cy.get('[data-testid="conversation-item"]').first().click();
    
    // Open participant filter
    cy.get('[data-testid="participant-filter"]').click();
    
    // Select a participant
    cy.get('[data-testid="participant-option"]').first().click();
    
    // Should only show messages from selected participant
    cy.get('[data-testid="message-item"]').each(($el) => {
      cy.wrap($el).find('[data-testid="message-sender"]').should('have.text', 'Alice');
    });
  });

  it('should export conversation', () => {
    // Navigate to a conversation
    cy.get('[data-testid="conversation-item"]').first().click();
    
    // Click export button
    cy.get('[data-testid="export-button"]').click();
    
    // Export dialog should appear
    cy.contains('Export Conversation').should('be.visible');
    
    // Select PDF format
    cy.get('[data-testid="export-format-pdf"]').click();
    
    // Enable options
    cy.get('[data-testid="include-analytics"]').check();
    cy.get('[data-testid="include-timestamps"]').check();
    
    // Submit export
    cy.get('[data-testid="export-submit"]').click();
    
    // Should show progress
    cy.contains('Exporting...').should('be.visible');
    
    // Should complete
    cy.contains('Export completed', { timeout: 10000 }).should('be.visible');
  });

  it('should delete conversation', () => {
    // Get initial count
    cy.get('[data-testid="conversation-item"]').then(($items) => {
      const initialCount = $items.length;
      
      // Click delete on first conversation
      cy.get('[data-testid="delete-conversation"]').first().click();
      
      // Confirm deletion
      cy.contains('Delete Conversation').should('be.visible');
      cy.get('[data-testid="confirm-delete"]').click();
      
      // Should show success message
      cy.contains('Conversation deleted').should('be.visible');
      
      // List should have one less item
      cy.get('[data-testid="conversation-item"]').should('have.length', initialCount - 1);
    });
  });

  it('should handle pagination', () => {
    // Assuming there are multiple pages
    cy.get('[data-testid="pagination"]').should('be.visible');
    
    // Click next page
    cy.get('[data-testid="next-page"]').click();
    
    // URL should update
    cy.url().should('include', 'page=2');
    
    // Different conversations should be shown
    cy.get('[data-testid="conversation-item"]').first().invoke('text').then((firstItemText) => {
      // Go back to first page
      cy.get('[data-testid="prev-page"]').click();
      
      // First item should be different
      cy.get('[data-testid="conversation-item"]').first().should('not.have.text', firstItemText);
    });
  });

  it('should bookmark messages', () => {
    // Navigate to a conversation
    cy.get('[data-testid="conversation-item"]').first().click();
    
    // Bookmark a message
    cy.get('[data-testid="bookmark-message"]').first().click();
    
    // Should show bookmark indicator
    cy.get('[data-testid="message-item"]').first().find('[data-testid="bookmark-icon"]').should('be.visible');
    
    // Navigate to bookmarks
    cy.get('[data-testid="view-bookmarks"]').click();
    
    // Should show bookmarked message
    cy.get('[data-testid="bookmarked-message"]').should('have.length.at.least', 1);
  });
});