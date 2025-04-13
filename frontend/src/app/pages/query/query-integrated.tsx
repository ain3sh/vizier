import { ReactElement, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  SendHorizonal, Trash2, Plus, Link,
  Check, XCircle
} from 'lucide-react';
import { queryAPI, draftAPI, Source, SourceReview } from '../../../services/api';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

// Define Phase type
type Phase = 'query_refinement' | 'source_refinement' | 'draft_review' | 'finalize';

// Define process stages
const PROCESS_STAGES = [
  { id: 'query_received', name: 'Query', description: 'Query received' },
  { id: 'refinement_completed', name: 'Refinement', description: 'Query refinement' },
  { id: 'source_review_ready', name: 'Sources', description: 'Source collection and review' },
  { id: 'draft_ready', name: 'Draft', description: 'Draft generation' },
  { id: 'draft_approved', name: 'Final', description: 'Draft approval' },
  { id: 'completed', name: 'Complete', description: 'Process completed' }
];

function QueryIntegrated() {
  // No need to use navigate if we're not navigating
  // const navigate = useNavigate();
  const urlInputRef = useRef<HTMLInputElement>(null);

  // Basic state
  const [searchValue, setSearchValue] = useState('');
  const [showOverlay, setOverlay] = useState(false);
  const [responseData, setResponseData] = useState('Please wait while we process your request.');
  const [currentPhase, setCurrentPhase] = useState<Phase>('query_refinement');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Query refinement states
  const [isQuerySatisfactory, setIsQuerySatisfactory] = useState(false);
  const [refinedQuery, setRefinedQuery] = useState<string | null>(null);
  const [isRefining, setIsRefining] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  
  // Query ID and processing states
  const [queryId, setQueryId] = useState<string | null>(null);
  const [currentStage, setCurrentStage] = useState<string | null>(null);
  
  // Sources states
  const [sources, setSources] = useState<Source[]>([]);
  const [openSourceIds, setOpenSourceIds] = useState<Set<string>>(new Set());
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [sourceUrl, setSourceUrl] = useState('');
  const [isAddingSource, setIsAddingSource] = useState(false);
  
  // Draft states
  const [draftId, setDraftId] = useState<string | null>(null);
  const [draftContent, setDraftContent] = useState('');
  const [isDraftGenerating, setIsDraftGenerating] = useState(false);

  // SSE refs
  const queryEventSourceRef = useRef<EventSource | null>(null);
  const draftEventSourceRef = useRef<EventSource | null>(null);

  // Focus URL input when shown
  useEffect(() => {
    if (showUrlInput && urlInputRef.current) {
      urlInputRef.current.focus();
    }
  }, [showUrlInput]);

  // Setup SSE for query progress
  useEffect(() => {
    if (!queryId) return;

    // Create query event source
    queryEventSourceRef.current = queryAPI.createEventSource(queryId);
    
    // Set up event handlers
    queryEventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.stage) {
          setCurrentStage(data.stage);
          
          // Handle stage transitions
          switch (data.stage) {
            case 'source_review_ready':
              setCurrentPhase('source_refinement');
              break;
            case 'draft_ready':
              if (data.data && data.data.draft_id) {
                setDraftId(data.data.draft_id);
                fetchDraft(data.data.draft_id);
              }
              setCurrentPhase('draft_review');
              break;
            case 'draft_approved':
              setCurrentPhase('finalize');
              break;
          }
        }
      } catch (err) {
        console.error('Error parsing query event:', err);
      }
    };
    
    queryEventSourceRef.current.onerror = (err) => {
      console.error('Query event source error:', err);
    };
    
    // Cleanup function
    return () => {
      if (queryEventSourceRef.current) {
        queryEventSourceRef.current.close();
      }
    };
  }, [queryId]);

  // Setup SSE for draft progress
  useEffect(() => {
    if (!draftId) return;

    // Create draft event source
    draftEventSourceRef.current = draftAPI.createEventSource(draftId);
    
    // Set up event handlers
    draftEventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'content_update' && data.content) {
          setDraftContent(data.content);
          if (data.is_completed) {
            setIsDraftGenerating(false);
          }
        }
      } catch (err) {
        console.error('Error parsing draft event:', err);
      }
    };
    
    draftEventSourceRef.current.onerror = (err) => {
      console.error('Draft event source error:', err);
    };
    
    // Cleanup function
    return () => {
      if (draftEventSourceRef.current) {
        draftEventSourceRef.current.close();
      }
    };
  }, [draftId]);

  // Fetch sources when needed
  useEffect(() => {
    if (currentPhase === 'source_refinement' && queryId) {
      fetchSources();
    }
  }, [currentPhase, queryId]);

  // Function to fetch sources
  const fetchSources = useCallback(async () => {
    if (!queryId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const sourcesData = await queryAPI.getSources(queryId);
      setSources(sourcesData);
    } catch (err) {
      console.error('Error fetching sources:', err);
      setError('Failed to fetch sources. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [queryId]);

  // Function to fetch draft content
  const fetchDraft = useCallback(async (id: string) => {
    try {
      const draft = await draftAPI.getDraft(id);
      setDraftContent(draft.content);
      setDraftId(draft.draft_id);
    } catch (err) {
      console.error('Error fetching draft:', err);
      setError('Failed to fetch draft content. Please try again.');
    }
  }, []);

  // Source management: toggle open/close
  const toggleSourceOpen = (sourceId: string) => {
    const newSet = new Set(openSourceIds);
    if (newSet.has(sourceId)) {
      newSet.delete(sourceId);
    } else {
      newSet.add(sourceId);
    }
    setOpenSourceIds(newSet);
  };

  // Add source via URL
  const addSource = () => {
    setShowUrlInput(true);
  };

  // Handle URL submission
  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceUrl.trim() || !queryId) return;
    
    setIsAddingSource(true);
    try {
      // Mock implementation - in a real app, you'd call an API endpoint
      const newSource: Source = {
        id: Date.now().toString(),
        title: 'New Source',
        url: sourceUrl,
        date: new Date().toISOString().split('T')[0],
        author: '',
        snippet: '',
        root: new URL(sourceUrl).hostname
      };
      
      setSources(prev => [...prev, newSource]);
      setSourceUrl('');
      setShowUrlInput(false);
    } catch (err) {
      console.error('Error adding source:', err);
      setError('Failed to add source. Please try again.');
    } finally {
      setIsAddingSource(false);
    }
  };

  // Cancel URL input
  const cancelUrlInput = () => {
    setShowUrlInput(false);
    setSourceUrl('');
  };

  // Remove a source
  const removeSource = (sourceId: string) => {
    setSources(prev => prev.filter(source => source.id !== sourceId));
    
    // Also remove from openSourceIds if it's there
    if (openSourceIds.has(sourceId)) {
      const newSet = new Set(openSourceIds);
      newSet.delete(sourceId);
      setOpenSourceIds(newSet);
    }
  };

  // Phase transition handlers
  const handleConfirm = async () => {
    if (currentPhase === 'query_refinement') {
      if (isQuerySatisfactory) {
        // User is satisfied with the refined query, move to next phase
        setCurrentPhase('source_refinement');
      } else {
        // Show refinement input if they want to refine further
        setIsRefining(true);
        if (refinedQuery) {
          setSearchValue(refinedQuery);
        }
      }
    } else if (currentPhase === 'source_refinement') {
      // Request draft generation
      try {
        setIsDraftGenerating(true);
        
        // Prepare source review
        const sourceReview: SourceReview = {
          included: sources.map(s => s.url),
          excluded: [],
          reranked_urls: sources.map(s => s.url)
        };
        
        // Submit source review
        await queryAPI.submitSourceReview(queryId as string, sourceReview);
        
        // Generate draft
        const draftResponse = await draftAPI.generateDraft(queryId as string);
        setDraftId(draftResponse.draft_id);
        
        // Move to draft review phase
        setCurrentPhase('draft_review');
        
        // Fetch the draft content
        fetchDraft(draftResponse.draft_id);
      } catch (err) {
        console.error('Error generating draft:', err);
        setError('Failed to generate draft. Please try again.');
      } finally {
        setIsDraftGenerating(false);
      }
    } else if (currentPhase === 'draft_review') {
      // Accept the draft
      if (draftId) {
        try {
          await draftAPI.acceptDraft(draftId);
          setCurrentPhase('finalize');
        } catch (err) {
          console.error('Error accepting draft:', err);
          setError('Failed to accept draft. Please try again.');
        }
      }
    } else if (currentPhase === 'finalize') {
      // Reset the app for a new query
      setOverlay(false);
      setResponseData('Please wait while we process your request.');
      setCurrentPhase('query_refinement');
      setIsQuerySatisfactory(false);
      setRefinedQuery(null);
      setConversationId(null);
      setQueryId(null);
      setSources([]);
      setOpenSourceIds(new Set());
      setDraftContent('');
      setDraftId(null);
    }
  };

  const handleDeny = () => {
    if (currentPhase === 'query_refinement') {
      setResponseData('Please wait while we process your request.');
      setOverlay(false);
      setIsRefining(false);
    } else if (currentPhase === 'source_refinement') {
      setCurrentPhase('query_refinement');
    } else if (currentPhase === 'draft_review') {
      setCurrentPhase('source_refinement');
    } else if (currentPhase === 'finalize') {
      setCurrentPhase('draft_review');
    }
  };

  // Submit search query
  const handleSend = async () => {
    if (searchValue.trim() === '') return;

    setOverlay(true);
    setCurrentPhase('query_refinement');
    setIsRefining(false);
    setIsLoading(true);
    setError(null);
    
    try {
      // Store the current query text
      const currentQuery = searchValue;
      setResponseData('Processing your query...');
      
      if (!queryId) {
        // Create a new query
        const newQueryId = await queryAPI.createQuery(currentQuery);
        setQueryId(newQueryId);
        
        // Now refine the query
        const refinementResult = await queryAPI.refineQuery(newQueryId, currentQuery);
        
        setRefinedQuery(refinementResult.refined_query);
        setConversationId(refinementResult.conversation_id || null);
        setIsQuerySatisfactory(true);
        setResponseData(`Your query is ready: ${refinementResult.refined_query}`);
      } else {
        // If queryId exists, provide feedback on the previous refinement
        const refinementResult = await queryAPI.refineQuery(queryId, currentQuery);
        
        setRefinedQuery(refinementResult.refined_query);
        setConversationId(refinementResult.conversation_id || null);
        setIsQuerySatisfactory(true);
        setResponseData(`Your query has been refined: ${refinementResult.refined_query}`);
      }
    } catch (err) {
      console.error('Error sending query:', err);
      setError('Failed to process query. Please try again.');
      setResponseData('Error processing your request. Please try again.');
      setIsQuerySatisfactory(false);
    } finally {
      setIsLoading(false);
      setSearchValue(''); // Clear input field
    }
  };

  // Handle search input changes
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(event.target.value);
  };

  // Handle Enter key press in search input
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSend();
    }
  };

  // Render confirmation buttons based on current phase
  const renderConfirmationButtons = () => {
    let confirmText = 'Next';
    let denyText = 'Back';
    
    if (currentPhase === 'query_refinement') {
      confirmText = isQuerySatisfactory ? 'Use This Query' : 'Refine Query';
      denyText = 'Cancel';
    } else if (currentPhase === 'source_refinement') {
      confirmText = 'Generate Draft';
    } else if (currentPhase === 'draft_review') {
      confirmText = 'Finalize';
    } else if (currentPhase === 'finalize') {
      confirmText = 'Done';
    }
    
    return (
      <div className="confirmation-buttons">
        <button className="deny-button" onClick={handleDeny} disabled={isLoading}>
          <XCircle size={16} />
          <span>{denyText}</span>
        </button>
        <button className="confirm-button" onClick={handleConfirm} disabled={isLoading}>
          <Check size={16} />
          <span>{confirmText}</span>
        </button>
      </div>
    );
  };

  // Input items for the query bar
  const queryItems: [string, ReactElement][] = [
    ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown} disabled={isLoading} />],
    ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend} style={{ opacity: isLoading ? 0.5 : 1 }} />]
  ];

  // Render progress bar
  const renderProgressBar = () => {
    const currentIndex = PROCESS_STAGES.findIndex(stage => stage.id === currentStage);
    const progress = currentIndex >= 0 ? (currentIndex / (PROCESS_STAGES.length - 1)) * 100 : 0;
    
    return (
      <div className="phase-progress">
        <div className="progress-steps">
          {PROCESS_STAGES.map((stage) => (
            <div 
              key={stage.id}
              className={`phase-step ${currentStage === stage.id ? 'active' : ''} 
                        ${PROCESS_STAGES.findIndex(s => s.id === currentStage) >= PROCESS_STAGES.findIndex(s => s.id === stage.id) ? 'completed' : ''}`}
              title={stage.description}
            >
              {stage.name}
            </div>
          ))}
        </div>
        <div className="progress-line">
          <div 
            className="progress-completed" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>
    );
  };

  // Render the current phase content
  const renderPhase = () => {
    switch (currentPhase) {
      case 'query_refinement':
        return (
          <div>
            <h3 className="query-title">{refinedQuery || ''}</h3>
            <div className="phase-card">
              <div className="phase-content">
                <div className="query-refinement-content">
                  <p className="query-text">{responseData}</p>
                  
                  {error && <div className="error-message">{error}</div>}
                  
                  {isRefining && !isQuerySatisfactory && (
                    <div className="query-refinement-input">
                      <input
                        type="text"
                        value={searchValue}
                        onChange={handleSearchChange}
                        onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        placeholder="Refine your query..."
                        className="refine-input"
                        disabled={isLoading}
                      />
                      <button 
                        className="refine-send-btn"
                        onClick={handleSend}
                        disabled={isLoading}
                      >
                        <SendHorizonal size={16} />
                        <span>Submit Refined Query</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'source_refinement':
        return (
          <div>
            <div className="phase-card">
              <div className="phase-header">
                <span>Sources</span>
              </div>
              <div className="phase-content">
                <div className="sources-content">
                  {isLoading ? (
                    <div className="loading">Loading sources...</div>
                  ) : error ? (
                    <div className="error-message">{error}</div>
                  ) : (
                    <>
                      <div className="sources-list">
                        {sources.map((source) => (
                          <div 
                            className="source-item" 
                            key={source.id}
                          >
                            <div className="source-header" onClick={() => toggleSourceOpen(source.id)}>
                              <div className="source-title-container">
                                <div className="source-title">
                                  {source.title || 'Untitled Source'}
                                  <span style={{display: 'inline-block', fontSize: '14px'}}>
                                    {source.root ? `| ${source.root}` : null}
                                  </span>
                                  <span style={{display: 'inline-block', fontSize: '14px'}}>
                                    {source.date ? `| ${source.date}` : null}
                                  </span>
                                </div>
                                <Trash2 
                                  size={14} 
                                  className="delete-icon" 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    removeSource(source.id);
                                  }} 
                                />
                              </div>
                              
                              {openSourceIds.has(source.id) && (
                                <div className="source-details">
                                  <div className="source-field">
                                    <span style={{color: 'gray', fontSize: '12px'}}>
                                      {source.url ? `${source.url} | ` : null}
                                    </span>
                                    <span style={{color: 'gray', fontSize: '12px'}}>
                                      {source.author ? `by ${source.author}` : null}
                                    </span>
                                  </div>
                                  <div className="source-field">
                                    <label>{source.snippet}</label>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      {showUrlInput ? (
                        <div className="url-input-container">
                          <form onSubmit={handleUrlSubmit}>
                            <div className="url-input-field">
                              <Link size={16} className="url-icon" />
                              <input 
                                type="url"
                                ref={urlInputRef}
                                placeholder="Enter URL to source..."
                                value={sourceUrl}
                                onChange={(e) => setSourceUrl(e.target.value)}
                                className="url-input"
                                disabled={isAddingSource}
                              />
                              <div className="url-input-actions">
                                <button 
                                  type="button"
                                  className="url-cancel-btn"
                                  onClick={cancelUrlInput}
                                  disabled={isAddingSource}
                                >
                                  <Trash2 size={16} />
                                </button>
                                <button 
                                  type="submit"
                                  className="url-add-btn"
                                  disabled={isAddingSource}
                                >
                                  {isAddingSource ? 'Processing...' : 'Add'}
                                </button>
                              </div>
                            </div>
                          </form>
                        </div>
                      ) : (
                        <button className="add-source-btn" onClick={addSource}>
                          <Plus size={14} /> Add Source
                        </button>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'draft_review':
        return (
          <div>
            <div className="phase-card">
              <div className="phase-header">
                <span>Draft</span>
              </div>
              <div className="phase-content">
                <div className="draft-text">
                  {isDraftGenerating ? 'Generating draft...' : draftContent}
                </div>
              </div>
            </div>
          </div>
        );

      case 'finalize':
        return (
          <div>
            <div className="phase-card">
              <div className="phase-header">
                <span>Finalize</span>
              </div>
              <div className="phase-content">
                <div className="finalize-options">
                  <p>Your research report is ready! Choose what to do next:</p>
                  
                  <div className="finalize-buttons">
                    <button className="finalize-option">
                      <span>Export PDF</span>
                    </button>
                    <button className="finalize-option">
                      <span>Share Link</span>
                    </button>
                    <button className="finalize-option">
                      <span>Save to Library</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  return (
    <div>
      {/* Overlay container */}
      <div className={`fade-container ${showOverlay ? 'overlay' : ''}`}>
        <div className={`overlay-content ${showOverlay ? 'visible' : ''}`}>
          {showOverlay && renderProgressBar()}
          <div className="phase-containers">
            {renderPhase()}
          </div>
        </div>
        {renderConfirmationButtons()}
      </div>

      {/* QueryBar container */}
      <div className={`query-bar-container ${showOverlay ? 'moved' : ''}`}>
        <QueryBar li={queryItems} />
      </div>
    </div>
  );
}

export default QueryIntegrated;