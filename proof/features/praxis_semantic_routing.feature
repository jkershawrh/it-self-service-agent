Feature: Govern self-service agent inference with semantic evidence

  Scenario: Shadow classification preserves existing behavior
    Given the self-service agent is configured with its baseline model route
    When llm-d-sc classifies an inference request in shadow mode
    Then the original model route is preserved
    And versioned semantic evidence is recorded for evaluation

  Scenario: A reasoning request uses an approved advanced model
    Given Praxis is enforcing the approved semantic routing policy
    When llm-d-sc ranks REASONING as the strongest complexity signal
    Then Praxis selects the advanced model route
    And the classifier does not provide an endpoint or final route

  Scenario: A restricted request remains on a private model route
    Given Praxis is enforcing the approved semantic routing policy
    When llm-d-sc ranks RESTRICTED as the strongest sensitivity signal
    Then Praxis selects the private model route
    And the policy decision is included in the audit evidence

  Scenario: Classifier abstention follows the safe fallback
    Given Praxis has a baseline model route
    When llm-d-sc abstains because context is insufficient
    Then Praxis preserves the baseline model route
    And the fallback reason is included in the audit evidence
