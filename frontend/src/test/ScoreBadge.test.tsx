import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ScoreBadge } from '../components/common/ScoreBadge';

describe('ScoreBadge', () => {
  it('renders internal relative ranking utility score without percentage formatting', () => {
    render(<ScoreBadge score={0.8421} />);
    
    // Must show utility score
    expect(screen.getByText('0.842')).toBeInTheDocument();
    expect(screen.getByText('Rank Utility:')).toBeInTheDocument();

    // UX Constraint: Never display raw playlist scores as confidence percentages (no % symbol)
    expect(screen.queryByText(/84\.2%/)).not.toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});
