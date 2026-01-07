describe('Favourites Management', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/auth/login')
    cy.get('input[name="email"]').type(Cypress.env('testMemberEmail'))
    cy.get('input[name="password"]').type(Cypress.env('testMemberPassword'))
    cy.get('button[type="submit"]').click()
    cy.url().should('eq', Cypress.config().baseUrl + '/')
  })

  it('should navigate to favourites page', () => {
    cy.contains('a', 'Meine Favoriten').click()
    cy.url().should('include', '/members/favourites')
    cy.contains('Meine Favoriten')
  })

  it('should display favourites list', () => {
    cy.visit('/members/favourites')
    cy.get('#favourites-list').should('be.visible')
  })

  it('should show add favourite button', () => {
    cy.visit('/members/favourites')
    cy.contains('button', 'Favorit hinzufügen').should('be.visible')
  })

  it('should open add favourite form', () => {
    cy.visit('/members/favourites')
    cy.contains('button', 'Favorit hinzufügen').click()
    cy.get('#add-favourite-form').should('not.have.class', 'hidden')
    cy.get('#favourite-member-select').should('be.visible')
  })

  it('should close add favourite form', () => {
    cy.visit('/members/favourites')
    cy.contains('button', 'Favorit hinzufügen').click()
    cy.get('#add-favourite-form').should('not.have.class', 'hidden')
    
    cy.contains('button', 'Abbrechen').click()
    cy.get('#add-favourite-form').should('have.class', 'hidden')
  })

  it('should only show non-favourite members in dropdown', () => {
    cy.visit('/members/favourites')
    cy.contains('button', 'Favorit hinzufügen').click()
    
    // Wait for dropdown to load
    cy.get('#favourite-member-select option').should('have.length.gt', 1)
    
    // Should not contain "Bitte wählen" as the only option
    cy.get('#favourite-member-select').should('not.contain', 'Alle Mitglieder sind bereits Favoriten')
  })

})
