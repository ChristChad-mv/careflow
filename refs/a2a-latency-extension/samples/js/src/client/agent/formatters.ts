import { AgentCard } from '@a2a-js/sdk';

export const formattedCards = (cards: AgentCard[]): string => {
  const formatted = cards.map((card, index) => {
    const lines: string[] = [];

    lines.push(`${index + 1}. Name: ${card.name || 'Unnamed Agent'}`);

    lines.push(
      `${' '.repeat(3)}Server URL: ${card.url?.replace(/\/+$/, '') || 'Unknown'}`,
    );
    lines.push(
      `${' '.repeat(3)}Description: ${card.description || 'No description provided'}`,
    );

    if (card.skills?.length) {
      lines.push(`${' '.repeat(3)}Skills:`);
      card.skills.forEach((skill) => {
        const header = `${skill.name}: ${skill.description}`;
        lines.push(`${' '.repeat(5)}- ${header}`);
        if (skill.examples?.length) {
          lines.push(`${' '.repeat(7)}Examples:`);
          skill.examples.forEach((example) => {
            lines.push(`${' '.repeat(9)}- ${example}`);
          });
        }
      });
    } else {
      lines.push(`${' '.repeat(3)}Skills: None`);
    }

    if (card.capabilities?.extensions?.length) {
      lines.push(`${' '.repeat(3)}Extensions:`);
      card.capabilities.extensions.forEach((extension) => {
        lines.push(
          `${' '.repeat(5)}- Description:${extension.description} (${extension.required ? 'Required' : 'Optional'})`,
        );
        if (extension.params) {
          lines.push(`${' '.repeat(7)}Params:`);
          const renderParams = (
            params: { [k: string]: unknown },
            baseIndent: number,
          ) => {
            Object.entries(params).forEach(([key, value]) => {
              if (Array.isArray(value)) {
                lines.push(
                  `${' '.repeat(baseIndent)}${key}: ${value.join(', ')}`,
                );
              } else if (value && typeof value === 'object') {
                // Display the parent key and increase indentation for nested entries
                lines.push(`${' '.repeat(baseIndent)}${key}:`);
                renderParams(value as { [k: string]: unknown }, baseIndent + 2);
              } else {
                lines.push(`${' '.repeat(baseIndent)}${key}: ${String(value)}`);
              }
            });
          };
          renderParams(extension.params, 9);
        }
      });
    } else {
      lines.push(`${' '.repeat(3)}Extensions: None`);
    }

    return lines.join('\n');
  });

  return formatted.join('\n\n');
};
