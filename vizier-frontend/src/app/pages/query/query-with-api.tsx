import { ReactElement, useState, useEffect, useRef } from 'react';
import { Textfit } from 'react-textfit';
import { 
  SendHorizonal, ChevronDown, ChevronRight, 
  X, Plus, GripVertical, Check, XCircle, Link 
} from 'lucide-react';
import axios from 'axios';
import QueryBar from '../../../components/querybar/querybar';

import './query.css';

// Define Source interface
interface Source {
  id: string;
  title: string;
  url: string;
  date: string;
  author: string;
  snippet: string;
  root: string;
}

// Define Phase type
type Phase = 'query_refinement' | 'source_refinement' | 'draft_review';

// API base URL - using the working API endpoint
const API_BASE_URL = 'http://localhost:8000';

function Query() {
    const [searchValue, setSearchValue] = useState(''); // State to track the input value
    const [showOverlay, setOverlay] = useState(false); // State to track the expanding animation
    const [responseData, setResponseData] = useState('Please wait while we process your request.'); // State to store API response
    const [currentPhase, setCurrentPhase] = useState<Phase>('query_refinement'); // Track the current phase
    
    // Add new state variables for query refinement
    const [isQuerySatisfactory, setIsQuerySatisfactory] = useState(false);
    const [queryFeedback, setQueryFeedback] = useState<string | null>(null);
    const [refinedQuery, setRefinedQuery] = useState<string | null>(null);
    const [isRefining, setIsRefining] = useState(false);
    
    // Collapsible states for each phase
    const [isQueryOpen, setIsQueryOpen] = useState(true);
    const [isSourcesOpen, setIsSourcesOpen] = useState(false);
    const [isDraftOpen, setIsDraftOpen] = useState(false);
    
    // Sources state
    const [sources, setSources] = useState<Source[]>([]);
    const [openSourceIds, setOpenSourceIds] = useState<Set<string>>(new Set());
    const [draggedItem, setDraggedItem] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Draft content
    const [draftContent, setDraftContent] = useState('');

    // Add new state for URL input
    const [showUrlInput, setShowUrlInput] = useState(false);
    const [sourceUrl, setSourceUrl] = useState('');
    const [isAddingSource, setIsAddingSource] = useState(false);
    const urlInputRef = useRef<HTMLInputElement>(null);
    
    // Add query ID state to track the current query
    const [queryId, setQueryId] = useState<string | null>(null);
    
    // Effect to focus the URL input field when it appears
    useEffect(() => {
        if (showUrlInput && urlInputRef.current) {
            urlInputRef.current.focus();
        }
    }, [showUrlInput]);
    
    // Fetch sources on component mount or phase change
    useEffect(() => {
        if (currentPhase === 'source_refinement' && queryId) {
            fetchSources();
            // Auto-collapse query section when moving to sources
            setIsQueryOpen(false);
            setIsSourcesOpen(true);
        } else if (currentPhase === 'draft_review' && queryId) {
            // Auto-collapse sources section when moving to draft
            setIsSourcesOpen(false);
            setIsDraftOpen(true);
            fetchDraft();
        }
    }, [currentPhase, queryId]);
    
    // Authentication header helper function
    const getAuthHeader = () => {
        const token = localStorage.getItem('jwt');
        return { headers: { Authorization: `Bearer ${token}` } };
    };
    
    // Phase transition handlers
    const handleConfirm = async () => {
        if (currentPhase === 'query_refinement') {
            if (isQuerySatisfactory) {
                setCurrentPhase('source_refinement');
            } else {
                // If query is not satisfactory, show refinement interface
                setIsRefining(true);
                if (refinedQuery) {
                    setSearchValue(refinedQuery);
                }
            }
        } else if (currentPhase === 'source_refinement') {
            // Generate draft from sources
            if (queryId) {
                try {
                    await axios.post(`${API_BASE_URL}/drafts/generate`, { query_id: queryId }, getAuthHeader());
                    setCurrentPhase('draft_review');
                } catch (error) {
                    console.error('Error generating draft:', error);
                    setError('Failed to generate draft. Please try again later.');
                }
            }
        } else if (currentPhase === 'draft_review') {
            // Here you would typically submit the final draft
            console.log('Final draft approved');
            // Reset the app
            setOverlay(false);
            setResponseData('Please wait while we process your request.');
            setCurrentPhase('query_refinement');
            setIsQuerySatisfactory(false);
            setRefinedQuery(null);
            setQueryFeedback(null);
        }
    };
    
    const handleDeny = () => {
        if (currentPhase === 'query_refinement') {
            // Reset query refinement
            setResponseData('Please wait while we process your request.');
            setOverlay(false);
        } else if (currentPhase === 'source_refinement') {
            // Go back to query refinement
            setCurrentPhase('query_refinement');
            setIsQueryOpen(true);
            setIsSourcesOpen(false);
        } else if (currentPhase === 'draft_review') {
            // Go back to source refinement
            setCurrentPhase('source_refinement');
            setIsSourcesOpen(true);
            setIsDraftOpen(false);
        }
    };
    
    // Fetch sources from API
    const fetchSources = async () => {
        if (!queryId) return;
        
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`${API_BASE_URL}/queries/${queryId}/sources`, getAuthHeader());
            console.log('Fetched sources:', response.data);
            
            // Handle the case where the response might be a string
            const parsedSources = typeof response.data === 'string' ? JSON.parse(response.data) : response.data;
            setSources(parsedSources);
        } catch (error) {
            console.error('Error fetching sources:', error);
            setError('Failed to load sources. Please try again later.');
        } finally {
            setIsLoading(false);
        }
    };
    
    // Fetch draft content
    const fetchDraft = async () => {
        if (!queryId) return;
        
        try {
            const response = await axios.get(`${API_BASE_URL}/drafts/${queryId}`, getAuthHeader());
            setDraftContent(response.data.content);
        } catch (error) {
            console.error('Error fetching draft:', error);
            setDraftContent('Draft unavailable. There may have been an error generating the content.');
        }
    };
    
    // Source handlers
    const toggleSourceOpen = (sourceId: string) => {
        const newOpenSourceIds = new Set(openSourceIds);
        if (newOpenSourceIds.has(sourceId)) {
            newOpenSourceIds.delete(sourceId);
        } else {
            newOpenSourceIds.add(sourceId);
        }
        setOpenSourceIds(newOpenSourceIds);
    };
    
    // Add source via URL
    const addSource = () => {
        // Simply show the URL input field
        setShowUrlInput(true);
    };
    
    const handleUrlSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!sourceUrl.trim() || !queryId) {
            return; // Don't submit empty URLs or if no queryId
        }
        
        setIsAddingSource(true);
        
        try {
            // Send the URL to the backend using the correct endpoint
            const response = await axios.post(`${API_BASE_URL}/queries/${queryId}/sources`, {
                url: sourceUrl
            }, getAuthHeader());
            
            console.log('Added source:', response.data);
            
            // Refresh sources to include the newly added one
            fetchSources();
            
            // Reset the URL input
            setSourceUrl('');
            setShowUrlInput(false);
        } catch (error) {
            console.error('Error adding source:', error);
            setError('Failed to add source. Please try again.');
        } finally {
            setIsAddingSource(false);
        }
    };
    
    const cancelUrlInput = () => {
        setSourceUrl('');
        setShowUrlInput(false);
    };
    
    const removeSource = async (sourceId: string) => {
        if (!queryId) return;
        
        try {
            // Optimistically update UI
            setSources(sources.filter(source => source.id !== sourceId));
            
            // Make API call to remove source
            await axios.delete(`${API_BASE_URL}/queries/${queryId}/sources/${sourceId}`, getAuthHeader());
            console.log('Removed source:', sourceId);
        } catch (error) {
            console.error('Error removing source:', error);
            fetchSources(); // Refresh sources if there was an error
        }
    };
    
    const updateSource = async (index: number, field: keyof Source, value: string) => {
        if (!queryId) return;
        
        const sourceToUpdate = sources[index];
        const updatedSource = { ...sourceToUpdate, [field]: value };
        
        try {
            // Optimistically update UI
            const newSources = [...sources];
            newSources[index] = updatedSource;
            setSources(newSources);
            
            // Make API call to update source
            await axios.put(`${API_BASE_URL}/queries/${queryId}/sources/${sourceToUpdate.id}`, updatedSource, getAuthHeader());
            console.log('Updated source:', updatedSource);
        } catch (error) {
            console.error('Error updating source:', error);
            fetchSources(); // Refresh sources if there was an error
        }
    };
    
    // Drag and drop handlers
    const handleDragStart = (index: number) => {
        setDraggedItem(index);
    };
    
    const handleDragOver = (e: React.DragEvent, index: number) => {
        e.preventDefault();
        
        if (draggedItem === null) return;
        
        const items = [...sources];
        const draggedItemContent = items[draggedItem];
        items.splice(draggedItem, 1);
        items.splice(index, 0, draggedItemContent);
        
        setDraggedItem(index);
        setSources(items);
    };
    
    const handleDragEnd = async () => {
        if (!queryId) return;
        
        setDraggedItem(null);
        
        try {
            // Make API call to update source order
            await axios.put(`${API_BASE_URL}/queries/${queryId}/sources/order`, {
                sourceIds: sources.map(source => source.id)
            }, getAuthHeader());
            console.log('Updated source order:', sources.map(source => source.id));
        } catch (error) {
            console.error('Error updating source order:', error);
            fetchSources(); // Refresh sources if there was an error
        }
    };

    const handleSend = async () => {
        if (searchValue.trim() === '') {
            return; // Empty input, do nothing
        }
        
        console.log('Send button pressed with input:', searchValue);
        setOverlay(true); // Trigger the expanding animation
        setCurrentPhase('query_refinement');
        setIsQueryOpen(true);
        setIsRefining(false);

        // Set overlay-title as query text
        const overlayTitle = document.querySelector('.overlay-title') as HTMLElement;
        if (overlayTitle) {
            overlayTitle.textContent = searchValue;
        }
        
        try {
            // First, create a new query
            setResponseData('Processing your query...');
            const createRes = await axios.post(`${API_BASE_URL}/queries`, { 
                initial_query: searchValue 
            }, getAuthHeader());
            
            const newQueryId = createRes.data.query_id;
            setQueryId(newQueryId);
            
            // Then, refine the query
            const refineRes = await axios.post(`${API_BASE_URL}/queries/${newQueryId}/refine`, { 
                query: searchValue 
            }, getAuthHeader());
            
            const refined = refineRes.data.refined_query;
            
            // Set UI states based on the response
            setIsQuerySatisfactory(true);
            setRefinedQuery(refined);
            setQueryFeedback(null);
            setResponseData(`Your query is ready: ${refined}`);
            
        } catch (error) {
            console.error('Error sending query:', error);
            setResponseData('Error processing your request. Please try again.');
            setIsQuerySatisfactory(false);
        }
        
        setSearchValue(''); // Clear input field
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSearchValue(event.target.value); // Update the state with the input value
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSend(); // Trigger the send action on Enter press
        }
    };
    
    // Render confirmation buttons based on current phase
    const renderConfirmationButtons = () => {
        let confirmText = 'Next';
        let denyText = 'Back';
        
        if (currentPhase === 'query_refinement') {
            denyText = 'Cancel';
        } else if (currentPhase === 'source_refinement') {
            confirmText = 'Generate Draft';
        } else if (currentPhase === 'draft_review') {
            confirmText = 'Approve Draft';
        }
        
        return (
            <div className="confirmation-buttons">
                <button className="deny-button" onClick={handleDeny}>
                    <XCircle size={16} />
                    <span>{denyText}</span>
                </button>
                <button className="confirm-button" onClick={handleConfirm}>
                    <Check size={16} />
                    <span>{confirmText}</span>
                </button>
            </div>
        );
    };

    const queryItems: [string, ReactElement][] = [
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={handleSearchChange} onKeyDown={handleKeyDown}/>],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend}/>],
    ];

    return (
        <div>
            {/* Overlay container */}
            <div className={`fade-container ${showOverlay ? 'overlay' : ''}`}>
                <div className={`overlay-content ${showOverlay ? 'visible' : ''}`}>
                    <Textfit 
                        mode="multi"
                        min={12}
                        max={48}
                        style={{
                            height: '100%',
                            width: '80%',
                        }}
                    >
                        <p className="overlay-title"></p>
                    </Textfit>
                    
                    {/* Phase containers - always show them all but control visibility with state */}
                    <div className="phase-containers">
                        {/* Query Refinement Phase */}
                        <div className="phase-card">
                            <div 
                                className="phase-header" 
                                onClick={() => setIsQueryOpen(!isQueryOpen)}
                            >
                                {isQueryOpen ? 
                                    <ChevronDown size={16} className="chevron-icon" /> : 
                                    <ChevronRight size={16} className="chevron-icon" />
                                }
                                <span>Query Refinement</span>
                            </div>
                            
                            {isQueryOpen && (
                                <div className="phase-content">
                                    <div className="query-refinement-content">
                                        <p className="query-text">{responseData}</p>
                                        
                                        {isRefining && !isQuerySatisfactory && (
                                            <div className="query-refinement-input">
                                                <input
                                                    type="text"
                                                    value={searchValue}
                                                    onChange={handleSearchChange}
                                                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                                    placeholder="Refine your query..."
                                                    className="refine-input"
                                                />
                                                <button 
                                                    className="refine-send-btn"
                                                    onClick={handleSend}
                                                >
                                                    <SendHorizonal size={16} />
                                                    <span>Submit Refined Query</span>
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                        
                        {/* Source Refinement Phase - only show if we're at or past this phase */}
                        {(currentPhase === 'source_refinement' || currentPhase === 'draft_review') && (
                            <div className="phase-card">
                                <div 
                                    className="phase-header" 
                                    onClick={() => setIsSourcesOpen(!isSourcesOpen)}
                                >
                                    {isSourcesOpen ? 
                                        <ChevronDown size={16} className="chevron-icon" /> : 
                                        <ChevronRight size={16} className="chevron-icon" />
                                    }
                                    <span>Sources</span>
                                </div>
                                
                                {isSourcesOpen && (
                                    <div className="phase-content">
                                        <div className="sources-content">
                                            {isLoading ? (
                                                <div className="loading-indicator">Loading sources...</div>
                                            ) : error ? (
                                                <div className="error-message">{error}</div>
                                            ) : (
                                                <>
                                                    <div className="sources-list">
                                                        {sources.map((source, index) => (
                                                            <div 
                                                                key={source.id}
                                                                className="source-item"
                                                                draggable={true}
                                                                onDragStart={() => handleDragStart(index)}
                                                                onDragOver={(e) => handleDragOver(e, index)}
                                                                onDragEnd={handleDragEnd}
                                                            >
                                                                <div className="source-card">
                                                                    <div className="source-header">
                                                                        <div className="drag-handle">
                                                                            <GripVertical size={14} />
                                                                        </div>
                                                                        <div 
                                                                            className="source-title"
                                                                            onClick={() => toggleSourceOpen(source.id)}
                                                                        >
                                                                            {openSourceIds.has(source.id) ? 
                                                                                <ChevronDown size={14} /> : 
                                                                                <ChevronRight size={14} />
                                                                            }
                                                                            
                                                                            <span>{source.title || 'Untitled Source'}</span>
                                                                            <span style={{display: 'inline-block', fontSize: '14px'}}>
                                                                                {source.root ?
                                                                                    `| ${source.root}` : null}
                                                                            </span>
                                                                            <span style={{display: 'inline-block', fontSize: '14px'}}>
                                                                                {source.date ?
                                                                                    `| ${source.date}` : null}
                                                                            </span>

                                                                        </div>
                                                                        <X 
                                                                            size={14} 
                                                                            className="delete-icon" 
                                                                            onClick={() => removeSource(source.id)} 
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
                                                    
                                                    {/* URL Input Field (conditionally rendered) */}
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
                                                                    />
                                                                    <div className="url-input-actions">
                                                                        <button 
                                                                            type="button"
                                                                            className="url-cancel-btn"
                                                                            onClick={cancelUrlInput}
                                                                            disabled={isAddingSource}
                                                                        >
                                                                            <X size={16} />
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
                                )}
                            </div>
                        )}
                        
                        {/* Draft Review Phase - only show if we're at this phase */}
                        {currentPhase === 'draft_review' && (
                            <div className="phase-card">
                                <div 
                                    className="phase-header" 
                                    onClick={() => setIsDraftOpen(!isDraftOpen)}
                                >
                                    {isDraftOpen ? 
                                        <ChevronDown size={16} className="chevron-icon" /> : 
                                        <ChevronRight size={16} className="chevron-icon" />
                                    }
                                    <span>Draft</span>
                                </div>
                                
                                {isDraftOpen && (
                                    <div className="phase-content">
                                        <div className="draft-content">
                                            <p className="draft-text">{draftContent}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                    
                    {/* Confirmation buttons */}
                    {renderConfirmationButtons()}
                </div>
            </div>

            {/* QueryBar container */}
            <div className={`query-bar-container ${showOverlay ? 'moved' : ''}`}>
                <QueryBar li={queryItems} />
            </div>
        </div>
    );
}

export default Query;