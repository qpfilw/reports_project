import type { PropsWithChildren, ReactNode } from 'react';

interface ContentCardProps extends PropsWithChildren {
  header?: ReactNode;
}

export function ContentCard({ header, children }: ContentCardProps) {
  return (
    <section className="content-card">
      {header ? <div className="content-card-header">{header}</div> : null}
      <div className="content-card-body">{children}</div>
    </section>
  );
}