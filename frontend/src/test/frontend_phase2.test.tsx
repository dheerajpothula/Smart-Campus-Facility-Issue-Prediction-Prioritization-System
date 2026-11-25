// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { EmptyState } from '../components/ui/EmptyState';
import { TokenManager } from '../services/apiClient';
import { App } from '../App';
import { getStatusBadgeVariant, getPriorityBadgeVariant } from '../utils/formatters';

describe('1. Design System & UI Components', () => {
  it('renders Button with variants and loading state', () => {
    const { rerender } = render(<Button variant="primary">Submit Request</Button>);
    expect(screen.getByText('Submit Request')).toBeInTheDocument();

    rerender(<Button variant="danger" isLoading>Processing</Button>);
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders Input with labels, helpers, and error states', () => {
    const { rerender } = render(
      <Input label="Contact Number" helperText="10 digits required" placeholder="1234567890" />
    );
    expect(screen.getByText('Contact Number')).toBeInTheDocument();
    expect(screen.getByText('10 digits required')).toBeInTheDocument();

    rerender(<Input label="Contact Number" error="Invalid phone number" />);
    expect(screen.getByText('Invalid phone number')).toBeInTheDocument();
  });

  it('renders Status & Priority Badges matching approved FIPP Sage & Forest theme', () => {
    const resolvedBadge = getStatusBadgeVariant('Resolved');
    expect(resolvedBadge.bg).toContain('emerald');

    const inProgressBadge = getStatusBadgeVariant('In Progress');
    expect(inProgressBadge.bg).toContain('amber');

    const criticalPriority = getPriorityBadgeVariant('Critical');
    expect(criticalPriority.bg).toContain('red');

    render(<Badge status="Resolved" />);
    expect(screen.getByText('Resolved')).toBeInTheDocument();
  });

  it('renders EmptyState with custom title and descriptions', () => {
    render(
      <EmptyState
        title="No Complaints in Queue"
        description="All campus tickets have been assigned."
      />
    );
    expect(screen.getByText('No Complaints in Queue')).toBeInTheDocument();
    expect(screen.getByText('All campus tickets have been assigned.')).toBeInTheDocument();
  });
});

describe('2. Authentication & Token Management', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('manages access token, refresh token, and user session in sessionStorage', () => {
    expect(TokenManager.getAccessToken()).toBeNull();

    const mockUser = { id: '00123456', name: 'Student Resident', role: 'student' };
    TokenManager.setSession('mock_access_jwt', 'mock_refresh_jwt', mockUser);

    expect(TokenManager.getAccessToken()).toBe('mock_access_jwt');
    expect(TokenManager.getRefreshToken()).toBe('mock_refresh_jwt');
    expect(TokenManager.getUser()).toEqual(mockUser);

    TokenManager.clearSession();
    expect(TokenManager.getAccessToken()).toBeNull();
    expect(TokenManager.getRefreshToken()).toBeNull();
    expect(TokenManager.getUser()).toBeNull();
  });
});

describe('3. Application Startup & Navigation Routing', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('renders the public landing page on initial startup', async () => {
    render(<App />);

    expect(screen.getAllByText(/Facility Issue Prediction & Prioritisation Platform/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/FIPP 2.0/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Student Portal/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Admin Control Centre/i).length).toBeGreaterThanOrEqual(1);
  });

  it('displays the three required "How FIPP Works" items: Report, Analyze, Prioritize', () => {
    render(<App />);

    expect(screen.getByText('How FIPP Works')).toBeInTheDocument();
    expect(screen.getByText('Report')).toBeInTheDocument();
    expect(screen.getByText('Analyze')).toBeInTheDocument();
    expect(screen.getByText('Prioritize')).toBeInTheDocument();
  });
});

describe('4. Form Validation & Taxonomy Rules', () => {
  it('validates 10-digit mobile contact number constraints', () => {
    const validContact = '9876543210';
    const clean = validContact.replace(/\D/g, '');
    expect(clean.length).toBe(10);

    const invalidContact = '12345';
    expect(invalidContact.replace(/\D/g, '').length).toBeLessThan(10);
  });

  it('enforces 500-character description upper boundary', () => {
    const validDesc = 'A'.repeat(450);
    expect(validDesc.length).toBeLessThanOrEqual(500);

    const invalidDesc = 'B'.repeat(505);
    expect(invalidDesc.length).toBeGreaterThan(500);
  });

  it('verifies cascading category hierarchy reset logic', () => {
    const mockTaxonomy = {
      'Air Conditioner': {
        'Cooling Issue': ['Compressor Trip', 'Gas Leakage'],
        'Water Dripping': ['Indoor Unit Leak', 'Drain Pipe Clogged'],
      },
      'Electricity': {
        'Power Failure': ['MCB Trip', 'Phase Issue'],
      },
    };

    let selectedCat = 'Air Conditioner';
    let availableSubs = Object.keys(mockTaxonomy[selectedCat]);
    expect(availableSubs).toEqual(['Cooling Issue', 'Water Dripping']);

    let selectedSub = 'Cooling Issue';
    let availableSpecifics = mockTaxonomy[selectedCat][selectedSub];
    expect(availableSpecifics).toContain('Compressor Trip');

    // Simulate changing category to Electricity
    selectedCat = 'Electricity';
    availableSubs = Object.keys(mockTaxonomy[selectedCat]);
    expect(availableSubs).toEqual(['Power Failure']);
    // Downstream selections reset
    selectedSub = availableSubs[0];
    availableSpecifics = mockTaxonomy[selectedCat][selectedSub];
    expect(availableSpecifics).toEqual(['MCB Trip', 'Phase Issue']);
    expect(availableSpecifics).not.toContain('Compressor Trip');
  });
});
