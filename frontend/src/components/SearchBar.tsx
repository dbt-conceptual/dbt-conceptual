import { useState, useCallback, useRef, useEffect } from 'react';
import { useStore } from '../store';

interface SearchResult {
  id: string;
  type: 'concept' | 'relationship';
  name: string;
  subtitle?: string;
}

interface SearchBarProps {
  onNavigate?: (id: string, type: 'concept' | 'relationship') => void;
}

export function SearchBar({ onNavigate }: SearchBarProps) {
  const { concepts, relationships, selectConcept, selectRelationship } = useStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Build search index from concepts and relationships
  const search = useCallback(
    (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      const lowerQuery = searchQuery.toLowerCase();
      const matches: SearchResult[] = [];

      // Search concepts
      for (const [id, concept] of Object.entries(concepts)) {
        const name = concept.name.toLowerCase();
        const domain = concept.domain?.toLowerCase() || '';
        if (name.includes(lowerQuery) || id.toLowerCase().includes(lowerQuery) || domain.includes(lowerQuery)) {
          matches.push({
            id,
            type: 'concept',
            name: concept.name,
            subtitle: concept.domain || undefined,
          });
        }
      }

      // Search relationships
      for (const [id, relationship] of Object.entries(relationships)) {
        const verb = relationship.verb.toLowerCase();
        const fromName = concepts[relationship.from_concept]?.name || relationship.from_concept;
        const toName = concepts[relationship.to_concept]?.name || relationship.to_concept;
        const searchText = `${verb} ${fromName} ${toName}`.toLowerCase();

        if (searchText.includes(lowerQuery) || id.toLowerCase().includes(lowerQuery)) {
          matches.push({
            id,
            type: 'relationship',
            name: relationship.verb,
            subtitle: `${fromName} → ${toName}`,
          });
        }
      }

      // Sort by relevance (exact matches first, then by name)
      matches.sort((a, b) => {
        const aExact = a.name.toLowerCase() === lowerQuery;
        const bExact = b.name.toLowerCase() === lowerQuery;
        if (aExact && !bExact) return -1;
        if (!aExact && bExact) return 1;
        return a.name.localeCompare(b.name);
      });

      // Limit results
      setResults(matches.slice(0, 10));
    },
    [concepts, relationships]
  );

  // Handle input change
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setQuery(value);
      search(value);
      setIsOpen(true);
      setSelectedIndex(0);
    },
    [search]
  );

  // Handle selection
  const handleSelect = useCallback(
    (result: SearchResult) => {
      if (result.type === 'concept') {
        selectConcept(result.id);
      } else {
        selectRelationship(result.id);
      }
      onNavigate?.(result.id, result.type);
      setQuery('');
      setResults([]);
      setIsOpen(false);
      inputRef.current?.blur();
    },
    [selectConcept, selectRelationship, onNavigate]
  );

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || results.length === 0) {
        if (e.key === 'Escape') {
          setQuery('');
          setIsOpen(false);
          inputRef.current?.blur();
        }
        return;
      }

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % results.length);
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + results.length) % results.length);
          break;
        case 'Enter':
          e.preventDefault();
          if (results[selectedIndex]) {
            handleSelect(results[selectedIndex]);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setQuery('');
          inputRef.current?.blur();
          break;
      }
    },
    [isOpen, results, selectedIndex, handleSelect]
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle focus
  const handleFocus = useCallback(() => {
    if (query.trim() && results.length > 0) {
      setIsOpen(true);
    }
  }, [query, results.length]);

  return (
    <div className="search-bar" ref={containerRef}>
      <input
        ref={inputRef}
        type="text"
        className="search-input"
        placeholder="Search concepts, relationships..."
        value={query}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
      />
      <span className="search-icon">{'\u{1F50D}'}</span>

      {isOpen && results.length > 0 && (
        <div className="search-dropdown">
          {results.map((result, index) => (
            <div
              key={`${result.type}-${result.id}`}
              className={`search-result ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleSelect(result)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="search-result-type">
                {result.type === 'concept' ? '\u25C7' : '\u2192'}
              </span>
              <div className="search-result-content">
                <div className="search-result-name">{result.name}</div>
                {result.subtitle && (
                  <div className="search-result-subtitle">{result.subtitle}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && query.trim() && results.length === 0 && (
        <div className="search-dropdown">
          <div className="search-no-results">No results found</div>
        </div>
      )}
    </div>
  );
}
