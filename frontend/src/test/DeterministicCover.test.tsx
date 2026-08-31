import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DeterministicCover } from '../components/common/DeterministicCover';

describe('DeterministicCover', () => {
  it('renders deterministic monogram placeholder without external image requests', () => {
    render(<DeterministicCover title="Solaris" artist="Cliff Martinez" album="Solaris OST" />);
    
    const cover = screen.getByTestId('deterministic-cover');
    expect(cover).toBeInTheDocument();
    expect(screen.getByText('S')).toBeInTheDocument();
    expect(cover).toHaveAttribute('title', 'Solaris by Cliff Martinez');
  });

  it('renders consistent style classes for identical track metadata', () => {
    const { container: c1 } = render(
      <DeterministicCover title="Nightcall" artist="Kavinsky" album="OutRun" />
    );
    const { container: c2 } = render(
      <DeterministicCover title="Nightcall" artist="Kavinsky" album="OutRun" />
    );

    expect(c1.innerHTML).toEqual(c2.innerHTML);
  });
});
