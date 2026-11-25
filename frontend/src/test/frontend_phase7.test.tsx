// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AdminOverviewPage } from '../pages/admin/AdminOverviewPage';
import { AdminAllRequestsPage } from '../pages/admin/AdminAllRequestsPage';
import { AdminReportsPage } from '../pages/admin/AdminReportsPage';
import { ComplaintDetailsDrawer } from '../components/admin/ComplaintDetailsDrawer';
import { ShapExplainabilityCard } from '../components/admin/intelligence/ShapExplainabilityCard';
import { StudentHistoryPage } from '../pages/student/StudentHistoryPage';
import { TokenManager } from '../services/apiClient';

const {
  mockKPIs,
  mockTickets,
  mockAnalytics,
  mockEmptyAnalytics,
  mockIntelOverview,
  mockComplaintIntelUnavailable,
  mockComplaintIntelAvailable,
} = vi.hoisted(() => {
  const kpis = {
    total: 3,
    new: 1,
    in_progress: 1,
    resolved: 1,
    withdrawn: 0,
    resolution_rate_percent: 33.3,
    average_turnaround_days: 2.0,
  };

  const mcpiSample = {
    scoring_type: 'Rule-Based Multi-Criteria Priority Index (MCPI)',
    is_ml_prediction: false,
    priority_score: 94.8,
    priority_tier: 'Critical',
    weights: {
      severity: 0.35,
      location_criticality: 0.25,
      recurrence_probability: 0.25,
      impact_population: 0.15,
    },
    thresholds: [
      { tier: 'Critical', rule: '>= 75.0', min_score: 75.0 },
      { tier: 'High', rule: '50.0 – 74.9', min_score: 50.0 },
      { tier: 'Medium', rule: '28.0 – 49.9', min_score: 28.0 },
      { tier: 'Low', rule: '< 28.0', min_score: 0.0 },
    ],
    components: [
      {
        key: 'severity',
        label: 'Severity',
        weight: 0.35,
        raw_label: 'Critical',
        normalized_input: 1.0,
        points: 35.0,
        max_points: 35.0,
      },
      {
        key: 'location_criticality',
        label: 'Location Criticality',
        weight: 0.25,
        raw_label: 'Server Room',
        normalized_input: 1.0,
        points: 25.0,
        max_points: 25.0,
      },
      {
        key: 'recurrence_probability',
        label: 'Recurrence Risk',
        weight: 0.25,
        raw_label: '85% risk factor',
        normalized_input: 0.85,
        points: 21.3,
        max_points: 25.0,
      },
      {
        key: 'impact_population',
        label: 'Population Impact',
        weight: 0.15,
        raw_label: '90% impact scale',
        normalized_input: 0.9,
        points: 13.5,
        max_points: 15.0,
      },
    ],
    classification_rationale:
      "Composite MCPI score of 94.8 / 100 maps to 'Critical' under threshold >= 75.0 (Critical).",
  };

  const tickets = [
    {
      complaint_id: 'CMP-2026-901',
      student_id: 'STU101',
      student_name: 'Rahul Sharma',
      category: 'Electricity',
      facility_type: 'Electricity',
      building: 'Academic Block 1',
      location: 'Academic Block 1 - Room 101',
      date_reported: '2026-11-24 10:00',
      status: 'Submitted' as const,
      priority_tier: 'Critical' as const,
      priority_score: 94.8,
      score_breakdown: {
        'Severity Contribution': 35.0,
        'Location Criticality Contribution': 25.0,
        'Recurrence Risk Contribution': 21.3,
        'Impact Population Contribution': 13.5,
      },
      mcpi_details: mcpiSample,
      description: 'Server room breaker sparking.',
      specific_categories: [],
      remarks_history: [],
      is_reopened: false,
      has_photo: false,
    },
  ];

  const analytics = {
    kpis,
    trends: [{ period: '2026-11-24', reported_count: 3, resolved_count: 1 }],
    category_distribution: [{ category: 'Electricity', count: 3, percentage: 100.0 }],
    location_distribution: [{ building: 'Academic Block 1', count: 3, percentage: 100.0 }],
    priority_distribution: { Critical: 1, High: 1, Medium: 1, Low: 0 },
    aging_brackets: { '<24h': 1, '1–3d': 1, '3–7d': 0, '>7d': 0 },
    workload_summary: {
      active_total: 2,
      unassigned_active: 1,
      assigned_active: 1,
      reopened_count: 1,
      average_mcpi_score: 62.4,
      active_average_mcpi_score: 79.0,
      high_critical_active: 2,
    },
    assignment_distribution: [
      { assignee: 'Ramesh Kumar', active_count: 1, resolved_count: 0, total_count: 1 },
      { assignee: 'Unassigned', active_count: 1, resolved_count: 0, total_count: 1 },
    ],
  };

  const emptyAnalytics = {
    kpis: {
      total: 0,
      new: 0,
      in_progress: 0,
      resolved: 0,
      withdrawn: 0,
      resolution_rate_percent: 0,
      average_turnaround_days: null,
    },
    trends: [],
    category_distribution: [],
    location_distribution: [],
    priority_distribution: { Critical: 0, High: 0, Medium: 0, Low: 0 },
    aging_brackets: { '<24h': 0, '1–3d': 0, '3–7d': 0, '>7d': 0 },
    workload_summary: {
      active_total: 0,
      unassigned_active: 0,
      assigned_active: 0,
      reopened_count: 0,
      average_mcpi_score: null,
      active_average_mcpi_score: null,
      high_critical_active: 0,
    },
    assignment_distribution: [],
  };

  const intelOverview = {
    capabilities: {
      mcpi_engine: {
        available: true,
        scoring_type: 'Rule-Based Multi-Criteria Priority Index (MCPI)',
        is_ml_prediction: false,
        weights: mcpiSample.weights,
        thresholds: mcpiSample.thresholds,
      },
      shap_explainability: {
        available: false,
        status: 'unavailable',
        reason: 'No serialized trained ML model artifacts exist in the model registry.',
        model_artifact_present: false,
        artifact_filenames: [],
        shap_library_installed: false,
      },
      auxiliary_models: {
        nlp_classifier: { holdout_accuracy: 0.4286, test_samples: 14 },
        severity_model: { holdout_accuracy: 0.375, test_samples: 8 },
      },
      predictive_forecasting: {
        available: false,
        status: 'unavailable',
        reason: 'Live failure-window forecasting is unavailable.',
      },
    },
    operational_analytics: analytics,
  };

  const complaintIntelUnavailable = {
    complaint_id: 'CMP-2026-901',
    mcpi: mcpiSample,
    shap: {
      complaint_id: 'CMP-2026-901',
      available: false,
      status: 'unavailable',
      reason: 'No serialized trained ML model artifacts exist and shap is not installed.',
      model_artifact_present: false,
      shap_library_installed: false,
      features: [],
      summary: 'SHAP feature attribution is unavailable.',
    },
  };

  const complaintIntelAvailable = {
    complaint_id: 'CMP-2026-901',
    available: true,
    status: 'available',
    reason: 'Active',
    model_artifact_present: true,
    shap_library_installed: true,
    model_version: 'v1.2',
    prediction_timestamp: '2026-11-25T14:30:00Z',
    prediction: 'Critical',
    base_value: 50.0,
    output_value: 88.5,
    features: [
      {
        feature_name: 'Hazard Keyword',
        feature_value: 'sparking',
        shap_value: 22.5,
        contribution: 'increase' as const,
        description: 'Positive impact on predicted severity.',
      },
    ],
    summary: 'Driven upward by Hazard Keyword.',
  };

  return {
    mockKPIs: kpis,
    mockTickets: tickets,
    mockAnalytics: analytics,
    mockEmptyAnalytics: emptyAnalytics,
    mockIntelOverview: intelOverview,
    mockComplaintIntelUnavailable: complaintIntelUnavailable,
    mockComplaintIntelAvailable: complaintIntelAvailable,
  };
});

vi.mock('../services/taxonomyService', () => ({
  taxonomyService: {
    getHierarchy: vi.fn().mockResolvedValue({
      maintenance_categories: ['Electricity', 'Plumbing'],
      campus_blocks: ['Academic Block 1', 'Hostel Block B'],
    }),
  },
}));

vi.mock('../services/complaintService', () => ({
  complaintService: {
    getAdminKPIs: vi.fn().mockResolvedValue(mockKPIs),
    getAllAdminComplaints: vi.fn().mockResolvedValue({
      total_count: mockTickets.length,
      limit: 15,
      offset: 0,
      records: mockTickets,
    }),
    getAnalyticsReport: vi.fn().mockResolvedValue(mockAnalytics),
    getStudentComplaints: vi.fn().mockResolvedValue({
      student_id: 'STU101',
      student_name: 'Rahul Sharma',
      total_complaints: 1,
      open_complaints: 1,
      closed_complaints: 0,
      records: mockTickets,
    }),
  },
}));

vi.mock('../services/intelligenceService', () => ({
  intelligenceService: {
    getOverview: vi.fn().mockResolvedValue(mockIntelOverview),
    getComplaintIntelligence: vi.fn().mockResolvedValue(mockComplaintIntelUnavailable),
  },
}));

describe('FIPP 2.0 Phase 7 — Predictive Intelligence Frontend Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    TokenManager.setSession('mock-admin-jwt', 'mock-refresh', {
      id: 'ADM-2026-001',
      role: 'admin',
      name: 'Administrator',
    });
  });

  it('1. renders authoritative MCPI points breakdown, rule-based label, and honest SHAP unavailable state in ComplaintDetailsDrawer', async () => {
    render(
      <ComplaintDetailsDrawer
        isOpen={true}
        ticket={mockTickets[0] as any}
        onClose={vi.fn()}
        onTicketUpdated={vi.fn()}
      />
    );

    expect(screen.getByText('Rule-Based Scoring (Non-ML)')).toBeDefined();
    expect(screen.getByText('Score: 94.8 / 100')).toBeDefined();
    expect(screen.getByText('35.0 pts')).toBeDefined();
    expect(screen.getByText('25.0 pts')).toBeDefined();
    expect(screen.getByText('21.3 pts')).toBeDefined();
    expect(screen.getByText('13.5 pts')).toBeDefined();

    await waitFor(() => {
      expect(screen.getByText('SHAP Feature Attribution Unavailable')).toBeDefined();
      expect(screen.getByText(/No serialized trained ML model artifacts exist/i)).toBeDefined();
    });
  });

  it('2. renders ShapExplainabilityCard available state with prediction, model version, and positive/negative contributions', () => {
    render(<ShapExplainabilityCard shap={mockComplaintIntelAvailable} loading={false} error={null} />);

    expect(screen.getByText('Model + SHAP Active')).toBeDefined();
    expect(screen.getByText('v1.2')).toBeDefined();
    expect(screen.getByText('Hazard Keyword (sparking)')).toBeDefined();
    expect(screen.getByText('+22.5 (Positive)')).toBeDefined();
  });

  it('3. renders Overview priority distribution, workload strip, and numeric MCPI score in All Requests', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <AdminOverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('MCPI Priority Distribution')).toBeDefined();
      expect(screen.getByText('Operational Workload Balance')).toBeDefined();
      expect(screen.getByText('Avg MCPI: 62.4')).toBeDefined();
    });
    unmount();

    render(
      <BrowserRouter>
        <AdminAllRequestsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('94.8')).toBeDefined();
      expect(screen.getAllByText('Critical').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('4. renders Reports assignment workload distribution, model status, and handles empty dataset safely', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <AdminReportsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('reports-workload-card')).toBeDefined();
      expect(screen.getByText('Ramesh Kumar')).toBeDefined();
      expect(screen.getAllByText('1 active • 0 resolved (1 total)').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByTestId('reports-model-diagnostics-card')).toBeDefined();
      expect(screen.getByText(/Active \(Rule-Based\)/i)).toBeDefined();
      expect(screen.getByText(/42\.9% holdout accuracy/i)).toBeDefined();
    });
    unmount();

    const { complaintService } = await import('../services/complaintService');
    vi.mocked(complaintService.getAnalyticsReport).mockResolvedValueOnce(mockEmptyAnalytics as any);

    render(
      <BrowserRouter>
        <AdminReportsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No assignment distribution records match the active filter.')).toBeDefined();
      expect(screen.getByText('Avg MCPI: Unavailable')).toBeDefined();
    });
  });

  it('5. ensures StudentHistoryPage does not expose MCPI scores, SHAP, or admin analytics', async () => {
    TokenManager.setSession('mock-stu-jwt', 'mock-refresh', {
      id: 'STU101',
      role: 'student',
      name: 'Rahul Sharma',
    });

    render(
      <BrowserRouter>
        <StudentHistoryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('CMP-2026-901')).toBeDefined();
    });

    expect(screen.queryByText(/MCPI/i)).toBeNull();
    expect(screen.queryByText(/SHAP/i)).toBeNull();
    expect(screen.queryByText('94.8')).toBeNull();
  });
});
