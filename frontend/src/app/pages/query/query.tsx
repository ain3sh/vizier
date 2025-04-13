import { ReactElement, useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  SendHorizonal, ChevronDown, ChevronRight, 
  Trash2, Plus, GripVertical, Check, XCircle, Link,
  Podcast, Share, StickyNote
} from 'lucide-react';
import { Tooltip } from '@mui/material';
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
type Phase = 'query_refinement' | 'source_refinement' | 'draft_review' | 'finalize';

// API base URL for your actual backend
const API_BASE_URL = 'http://localhost:';

function Query() {
    const navigate = useNavigate();
    // -- State variables --
    const [searchValue, setSearchValue] = useState('');
    const [showOverlay, setOverlay] = useState(false);
    const [responseData, setResponseData] = useState('Please wait while we process your request.');
    const [currentPhase, setCurrentPhase] = useState<Phase>('query_refinement');
    
    // Query refinement states
    const [isQuerySatisfactory, setIsQuerySatisfactory] = useState(false);
    const [refinedQuery, setRefinedQuery] = useState<string | null>(null);
    const [isRefining, setIsRefining] = useState(false);
    
    // New state variable to store query ID once a query is created
    const [queryId, setQueryId] = useState<string | null>(null);
    
    // Sources state
    const [sources, setSources] = useState<Source[]>([]);
    const [openSourceIds, setOpenSourceIds] = useState<Set<string>>(new Set());
    const [draggedItem, setDraggedItem] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    // Draft content state
    const [draftContent, setDraftContent] = useState('');

    // URL input state for adding new sources
    const [showUrlInput, setShowUrlInput] = useState(false);
    const [sourceUrl, setSourceUrl] = useState('');
    const [isAddingSource, setIsAddingSource] = useState(false);
    const urlInputRef = useRef<HTMLInputElement>(null);
    
    // Finalize phase states (Podcast, Share, Post)
    const [isPodcastGenerating, setIsPodcastGenerating] = useState(false);
    const [podcastUrl, setPodcastUrl] = useState<string | null>(null);
    const [isSharing, setIsSharing] = useState(false);
    const [shareUrl, setShareUrl] = useState<string | null>(null);
    const [isPosting, setIsPosting] = useState(false);
    const [postResult, setPostResult] = useState<string | null>(null);
    
    // -- Effect: Focus URL input when shown --
    useEffect(() => {
        if (showUrlInput && urlInputRef.current) {
            urlInputRef.current.focus();
        }
    }, [showUrlInput]);

    const getAuthHeader = useCallback(() => {
        const token = localStorage.getItem('jwt');
        return { headers: { Authorization: `Bearer ${token}` } };
    }, []);

    // -- Fetch sources from the backend --
    const fetchSources = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`${API_BASE_URL}/queries/${queryId}/sources`, getAuthHeader());
            const sourcesData = typeof response.data === 'string' ? JSON.parse(response.data) : response.data;
            setSources(sourcesData);
            console.log('goofy');
        } catch (err) {
            console.error('Error fetching sources:', err);
            const sourcesData = [
                {
                    "id": "13d8cb8c-7e9e-4a25-9a5b-81c5e1e5a7cd",
                    "url": "https://arxiv.org/abs/2303.00745",
                    "date": "2023-03-02",
                    "name": "arXiv",
                    "root": "arxiv.org",
                    "title": "Comparing Classical and Quantum Machine Learning for Molecular Property Prediction",
                    "author": "S. Johri et al.",
                    "snippet": "This study benchmarks classical and quantum ML models across molecular datasets, highlighting the performance tradeoffs on QM9 and MD17."
                },
                {
                    "id": "8c50c72a-643d-4658-947a-02b657d0ae89",
                    "url": "https://www.nature.com/articles/s41467-022-29693-y",
                    "date": "2022-04-12",
                    "name": "Nature Communications",
                    "root": "nature.com",
                    "title": "Quantum chemistry calculations on a superconducting quantum processor",
                    "author": "Kandala et al.",
                    "snippet": "IBM's quantum processor is used to simulate molecular ground states with VQE, demonstrating hardware-specific performance bottlenecks."
                },
                {
                    "id": "2fb5b5fc-1ae4-4a1e-a6c1-066f8caa17bb",
                    "url": "https://www.sciencedirect.com/science/article/pii/S0010465521001692",
                    "date": "2021-05-01",
                    "name": "Computer Physics Communications",
                    "root": "sciencedirect.com",
                    "title": "SchNetPack: A Deep Learning Toolbox For Atomistic Systems",
                    "author": "A. T. Unke et al.",
                    "snippet": "Presents SchNetPack, a modular toolbox implementing neural networks like SchNet for fast and accurate quantum chemistry predictions."
                }
                ];
            setSources(sourcesData);
            console.log('Set sources: ', sourcesData);
        } finally {
            setIsLoading(false);
            console.log('here');
        }
    }, [queryId, getAuthHeader]);

    // -- Fetch draft content from the backend --
    const fetchDraft = useCallback(async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/drafts/${queryId}`, getAuthHeader());
            setDraftContent(response.data.content);
        } catch (error) {
            console.error('Error fetching draft:', error);
            setDraftContent(`Response: Refined Research Plan – Comparative Analysis of Pure Quantum, Quantum Machine Learning (QML), and Classical Machine Learning Approaches in Quantum Chemistry

Overview
This research plan aims to provide a systematic and technically grounded comparative analysis of three major paradigms in quantum chemistry computation: (1) pure quantum algorithms, (2) quantum-enhanced machine learning models (QML), and (3) classical machine learning approaches. The focus is on benchmarking accuracy, scalability, and applicability across key tasks in molecular modeling and materials discovery.

1. Technical Foundations and Methodology
a. Pure Quantum Approaches
We will review leading quantum algorithms such as Variational Quantum Eigensolver (VQE), Quantum Phase Estimation (QPE), and Density Matrix Embedding Theory (DMET). Emphasis will be placed on their suitability for near-term quantum devices (NISQ), quantum circuit depth and width requirements, and recent improvements in error mitigation and variational ansätze.

b. QML Approaches
Survey of hybrid quantum-classical models including quantum kernel methods (e.g., QSVMs), quantum neural networks (QNNs), and variational quantum classifiers. Evaluation will focus on claimed or demonstrated quantum advantage in regression and classification tasks, along with theoretical work on expressivity and generalization bounds.

c. Classical ML Approaches
Analysis of cutting-edge deep learning models like SchNet, PhysNet, DeepMD, and MPNNs. Benchmarks will include their ability to predict molecular energies, forces, and other quantum observables, as well as their scalability to larger molecular systems and data efficiency on datasets like QM9 and ANI-1x.

2. Performance Benchmarks and Comparative Studies
We will curate and synthesize results from peer-reviewed studies (2022–present) that directly compare these paradigms. Comparative metrics will include:

Accuracy: Energy/force prediction MAEs, orbital density errors

Scalability: Performance with system size, qubit count, and model parameters

Generalization: Cross-molecule and out-of-distribution robustness

Computational Resources: Wall-clock time, quantum/classical hardware use, training efficiency

Datasets of focus: QM7, QM9, ANI-1x, MD17.

3. Application Domains
Each paradigm will be evaluated in real-world quantum chemistry scenarios:

Molecular property prediction: HOMO-LUMO gaps, dipole moments, vibrational modes

Reaction pathway modeling: Transition state search using PES predictions

Materials and drug discovery: Ligand binding affinity, conformational sampling, catalyst design

4. Key Experts and Research Groups
Pure Quantum: Aspuru-Guzik (U Toronto), Garnet Chan (Caltech), IBM Quantum, Google Quantum AI

QML: Maria Schuld & Nathan Killoran (Xanadu), Giuseppe Carleo (EPFL), Kristan Temme (IBM)

Classical ML: Klaus-Robert Müller (TU Berlin), Anatole von Lilienfeld (U Vienna), DeepMind, Microsoft Research

Their latest publications, talks, and GitHub repositories will be used as primary technical sources.

5. Temporal Focus
The primary literature corpus will center on work from 2022 to present, including arXiv preprints and conference proceedings (NeurIPS, ICML, ACS, PRX Quantum). Earlier foundational papers (2017–2021) will be referenced to contextualize methods and trace algorithmic evolution.

6. Technical Depth and Implementation
This research will include a hands-on component:

Reproducing or extending open-source implementations (Qiskit, PennyLane, DeepChem)

Running small-scale quantum experiments on IBM Q / IonQ simulators

Benchmarking ML models in PyTorch/TensorFlow on quantum chemistry datasets

Analyzing scaling behavior with increasing molecular complexity

All implementations and evaluations will be documented with clear technical rationale to support reproducibility and transparency.

`);
        }
    }, [queryId, getAuthHeader]);

    // -- Effect: Fetch sources or draft content when phase changes --
    useEffect(() => {
        if (currentPhase === 'source_refinement') {
            fetchSources();
        } else if (currentPhase === 'draft_review') {
            fetchDraft();
        }
    }, [currentPhase, queryId, fetchSources, fetchDraft]);

    // -- Phase transition handlers --
    const handleConfirm = () => {
        if (currentPhase === 'query_refinement') {
            if (isQuerySatisfactory) {
                // Store current state in sessionStorage before navigating
                const stateToStore = {
                    currentPhase,
                    isQuerySatisfactory,
                    refinedQuery,
                    searchValue,
                    responseData,
                    queryId
                };
                sessionStorage.setItem('queryState', JSON.stringify(stateToStore));
                navigate('/graph');
            } else {
                setIsRefining(true);
                if (refinedQuery) {
                    setSearchValue(refinedQuery);
                }
            }
        } else if (currentPhase === 'source_refinement') {
            setCurrentPhase('draft_review');
        } else if (currentPhase === 'draft_review') {
            setCurrentPhase('finalize');
        } else if (currentPhase === 'finalize') {
            // Reset the app for a new query
            setOverlay(false);
            setResponseData('Please wait while we process your request.');
            setCurrentPhase('query_refinement');
            setIsQuerySatisfactory(false);
            setRefinedQuery(null);
            setPodcastUrl(null);
            setShareUrl(null);
            setPostResult(null);
            setQueryId(null);
            setSources([]);
            setDraftContent('');
        }
    };

    // Add effect to restore state when returning from graph
    useEffect(() => {
        const savedState = sessionStorage.getItem('queryState');
        if (savedState) {
            const {
                isQuerySatisfactory,
                refinedQuery,
                searchValue,
                responseData,
                queryId
            } = JSON.parse(savedState);
            
            // Always set to source refinement phase when returning from graph
            setCurrentPhase('source_refinement');
            setIsQuerySatisfactory(isQuerySatisfactory);
            setRefinedQuery(refinedQuery);
            setSearchValue(searchValue);
            setResponseData(responseData);
            setQueryId(queryId);
            setOverlay(true);
            
            // Clear the saved state
            sessionStorage.removeItem('queryState');
        }
    }, []);

    const handleDeny = () => {
        if (currentPhase === 'query_refinement') {
            setResponseData('Please wait while we process your request.');
            setOverlay(false);
        } else if (currentPhase === 'source_refinement') {
            setCurrentPhase('query_refinement');
        } else if (currentPhase === 'draft_review') {
            setCurrentPhase('source_refinement');
        } else if (currentPhase === 'finalize') {
            setCurrentPhase('draft_review');
        }
    };

    // -- Query submission: create and refine --
    const handleSend = async () => {
        if (searchValue.trim() === '') return;

        setOverlay(true);
        setCurrentPhase('query_refinement');
        setIsRefining(false);
        const currentQuery = searchValue;

        try {
            // If no query has been created yet, create one with POST /queries.
            if (!queryId) {
                const createRes = await axios.post(`${API_BASE_URL}/queries`, {
                    initial_query: currentQuery
                },  getAuthHeader());
                // Save the returned query_id in state.
                setQueryId(createRes.data.query_id);
            }

            console.log(queryId)
            
            // Now call the refinement endpoint using the query_id:
            const refineRes = await axios.post(`${API_BASE_URL}/queries/${queryId || ''}/refine`, {
                query: currentQuery
            },  getAuthHeader());
            
            // Assume the response returns a refined query.
            if (refineRes.data.refined_query) {
                setRefinedQuery(refineRes.data.refined_query);
                // Set the query as satisfactory (you can add extra logic based on backend flags).
                setIsQuerySatisfactory(true);
                setResponseData(`Your query is ready: "${refineRes.data.refined_query}"`);
            } else {
                setIsQuerySatisfactory(false);
                setResponseData('Query refinement needed.');
            }
        } catch (error) {
            console.error('Error sending query:', error);
            setResponseData(`Refined Research Plan: Comparative Analysis of Pure Quantum, Quantum Machine Learning (QML), and Classical Machine Learning Approaches in Quantum Chemistry

Key Research Components:

1. Technical Foundations and Methodology
   a. Pure Quantum Approaches: Investigate state-of-the-art quantum algorithms for electronic structure calculations (e.g., VQE, QPE, DMET), their hardware requirements, and scaling behavior.
   b. QML Approaches: Review quantum-enhanced machine learning models applied to quantum chemistry tasks (e.g., quantum kernel methods, quantum neural networks, hybrid quantum-classical models), focusing on demonstrated or theoretically projected quantum advantage.
   c. Classical ML Approaches: Examine leading classical ML models for quantum chemistry (e.g., SchNet, PhysNet, DeepMD, message passing neural networks), their data requirements, accuracy benchmarks, and computational efficiency.

2. Performance Benchmarks and Comparative Studies
   a. Identify recent peer-reviewed head-to-head studies or benchmarks comparing these three paradigms on standard quantum chemistry datasets (QM7, QM9, ANI-1, etc.).
   b. Specify metrics of comparison: accuracy (e.g., energy prediction errors), scalability, generalization, data efficiency, and computational resources (classical vs. quantum hardware).

3. Application Domains & Real-World Use Cases
   a. Molecular property prediction (energies, forces, electronic densities)
   b. Reaction pathway discovery and transition state search
   c. Materials discovery and drug design

4. Key Experts, Research Groups, and Institutions
   a. Pure Quantum: Aspuru-Guzik Group (U Toronto), Alán Aspuru-Guzik, Garnet Chan (Caltech), IBM Quantum, Google Quantum AI.
   b. QML: Maria Schuld (Xanadu), Nathan Killoran (Xanadu), Giuseppe Carleo (EPFL), Kristan Temme (IBM).
   c. Classical ML in Chemistry: Klaus-Robert Müller (TU Berlin), O. Anatole von Lilienfeld (University of Vienna), DeepMind, Microsoft Research.

5. Temporal Focus
   a. Emphasize research from the past 18–24 months (2022–present) to capture recent breakthroughs, preprints, and new benchmarks.
   b. Include foundational works (2017–2021) for methodological context where needed.

6. Technical Depth and Implementation
   a. Prioritize detailed technical analyses and implementation details`);
            setIsQuerySatisfactory(true);
        }
        
        // Clear the input field once done.
        setSearchValue('');
    };

    // -- Source management: add, remove, drag/reorder --
    const toggleSourceOpen = (sourceId: string) => {
        const newSet = new Set(openSourceIds);
        if (newSet.has(sourceId)) {
            newSet.delete(sourceId);
        } else {
            newSet.add(sourceId);
        }
        setOpenSourceIds(newSet);
    };

    // For this example, the add source functionality is handled locally.
    // (Later you can call a backend endpoint—e.g. attach/update source set.)
    const addSource = () => {
        setShowUrlInput(true);
    };

    const handleUrlSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!sourceUrl.trim()) return;

        setIsAddingSource(true);
        try {
            // Create a new source object from the provided URL.
            const newSource: Source = {
                id: Date.now().toString(),
                title: 'New Source',
                url: sourceUrl,
                date: new Date().toISOString().split('T')[0],
                author: '',
                snippet: '',
                root: new URL(sourceUrl).hostname
            };
            // Append the new source to the existing list.
            const updatedSources = [...sources, newSource];
            setSources(updatedSources);
            // Optionally, update the backend with the new source set.
            setSourceUrl('');
            setShowUrlInput(false);
        } catch (error) {
            console.error('Error processing URL:', error);
        } finally {
            setIsAddingSource(false);
        }
    };

    const cancelUrlInput = () => {
        setSourceUrl('');
        setShowUrlInput(false);
    };

    // Remove source locally (backend update can be added later)
    const removeSource = async (sourceId: string) => {
        setSources(sources.filter(source => source.id !== sourceId));
    };

    // Drag and drop handlers for source ordering
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
        setDraggedItem(null);
        // If you later implement a backend endpoint for ordering,
        // you can call it here with the new order.
    };

    // -- Finalize phase handlers (Podcast, Share, Post) remain unchanged --
    const generatePodcast = async () => {
        setIsPodcastGenerating(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/generate-podcast`, {
                content: draftContent,
                sources: sources
            },  getAuthHeader());
            setPodcastUrl(response.data.podcastUrl);
        } catch (error) {
            console.error('Error generating podcast:', error);
            setTimeout(() => {
                setPodcastUrl('https://example.com/sample-podcast.mp3');
            }, 1500);
        } finally {
            setIsPodcastGenerating(false);
        }
    };

    const shareContent = async () => {
        setIsSharing(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/share`, {
                content: draftContent,
                sources: sources
            });
            setShareUrl(response.data.shareUrl);
        } catch (error) {
            console.error('Error sharing content:', error);
            setTimeout(() => {
                setShareUrl('https://share.example.com/document/abc123');
            }, 1000);
        } finally {
            setIsSharing(false);
        }
    };

    const postContent = async () => {
        setIsPosting(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/post`, {
                content: draftContent,
                sources: sources.map(source => source.id)
            });
            setPostResult(response.data.message || 'Content posted successfully');
        } catch (error) {
            console.error('Error posting content:', error);
            setTimeout(() => {
                setPostResult('Content posted successfully (demo)');
            }, 1500);
        } finally {
            setIsPosting(false);
        }
    };

    // -- Render confirmation buttons based on the current phase --
    const renderConfirmationButtons = () => {
        let confirmText = 'Confirm';
        let denyText = 'Deny';
        
        if (currentPhase === 'query_refinement') {
            confirmText = isQuerySatisfactory ? 'Use This Query' : 'Refine Query';
            denyText = 'Cancel';
        } else if (currentPhase === 'source_refinement') {
            confirmText = 'Generate Draft';
            denyText = 'Back to Query';
        } else if (currentPhase === 'draft_review') {
            confirmText = 'Finalize';
            denyText = 'Back to Sources';
        } else if (currentPhase === 'finalize') {
            confirmText = 'Done';
            denyText = 'Back to Draft';
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
        ['Search', <input type="text" className="search-input" placeholder="Ask anything..." value={searchValue} onChange={(e) => setSearchValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }} />],
        ['Enter', <SendHorizonal size={40} className="send-btn" onClick={handleSend} />]
    ];

    const renderProgressBar = () => {
        const phases = ['Query', 'Sources', 'Draft', 'Finalize'];
        const currentIndex = 
            currentPhase === 'query_refinement' ? 0 : 
            currentPhase === 'source_refinement' ? 1 : 
            currentPhase === 'draft_review' ? 2 : 3;
            
        return (
            <div className="phase-progress">
                <div className="progress-steps">
                    {phases.map((phase, index) => (
                        <div 
                            key={phase}
                            className={`phase-step ${currentIndex === index ? 'active' : ''}`}
                        >
                            {phase}
                        </div>
                    ))}
                </div>
                <div className="progress-line">
                    <div 
                        className="progress-completed" 
                        style={{ width: `${(currentIndex * 100) / 3}%` }}
                    ></div>
                </div>
            </div>
        );
    };

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
                                    {isRefining && !isQuerySatisfactory && (
                                        <div className="query-refinement-input">
                                            <input
                                                type="text"
                                                value={searchValue}
                                                onChange={(e) => setSearchValue(e.target.value)}
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
                                                                        {source.root ? `| ${source.root}` : null}
                                                                    </span>
                                                                    <span style={{display: 'inline-block', fontSize: '14px'}}>
                                                                        {source.date ? `| ${source.date}` : null}
                                                                    </span>
                                                                </div>
                                                                <Trash2 
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
                                    {draftContent}
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
                                <div className="action-icons">
                                    <Tooltip title="Generate Podcast" arrow>
                                        <span style={{ display: 'inline-block', margin: '0 8px', cursor: 'pointer' }}>
                                            {podcastUrl ? (
                                                <a href={podcastUrl} target="_blank" rel="noopener noreferrer">
                                                    <Podcast size={20} />
                                                </a>
                                            ) : (
                                                <Podcast 
                                                    size={20} 
                                                    onClick={generatePodcast}
                                                    style={{ opacity: isPodcastGenerating ? 0.5 : 1 }}
                                                />
                                            )}
                                        </span>
                                    </Tooltip>
                                    
                                    <Tooltip title="Share Content" arrow>
                                        <span style={{ display: 'inline-block', margin: '0 8px', cursor: 'pointer' }}>
                                            {shareUrl ? (
                                                <a href={shareUrl} target="_blank" rel="noopener noreferrer">
                                                    <Share size={20} />
                                                </a>
                                            ) : (
                                                <Share 
                                                    size={20} 
                                                    onClick={shareContent}
                                                    style={{ opacity: isSharing ? 0.5 : 1 }}
                                                />
                                            )}
                                        </span>
                                    </Tooltip>
                                    
                                    <Tooltip title="Post Content" arrow>
                                        <span style={{ display: 'inline-block', margin: '0 8px', cursor: 'pointer' }}>
                                            <StickyNote 
                                                size={20} 
                                                onClick={postContent}
                                                style={{ opacity: isPosting || postResult ? 0.5 : 1 }}
                                            />
                                        </span>
                                    </Tooltip>
                                </div>
                            </div>
                            <div className="phase-content">
                                <div className="finalize-content">
                                    <div className="finalized-draft">
                                        <h3>Final Content</h3>
                                        <div className="finalize-text">
                                            {draftContent}
                                            
Overview
This research plan aims to provide a systematic and technically grounded comparative analysis of three major paradigms in quantum chemistry computation: (1) pure quantum algorithms, (2) quantum-enhanced machine learning models (QML), and (3) classical machine learning approaches. The focus is on benchmarking accuracy, scalability, and applicability across key tasks in molecular modeling and materials discovery.

1. Technical Foundations and Methodology
a. Pure Quantum Approaches
We will review leading quantum algorithms such as Variational Quantum Eigensolver (VQE), Quantum Phase Estimation (QPE), and Density Matrix Embedding Theory (DMET). Emphasis will be placed on their suitability for near-term quantum devices (NISQ), quantum circuit depth and width requirements, and recent improvements in error mitigation and variational ansätze.

b. QML Approaches
Survey of hybrid quantum-classical models including quantum kernel methods (e.g., QSVMs), quantum neural networks (QNNs), and variational quantum classifiers. Evaluation will focus on claimed or demonstrated quantum advantage in regression and classification tasks, along with theoretical work on expressivity and generalization bounds.

c. Classical ML Approaches
Analysis of cutting-edge deep learning models like SchNet, PhysNet, DeepMD, and MPNNs. Benchmarks will include their ability to predict molecular energies, forces, and other quantum observables, as well as their scalability to larger molecular systems and data efficiency on datasets like QM9 and ANI-1x.

2. Performance Benchmarks and Comparative Studies
We will curate and synthesize results from peer-reviewed studies (2022–present) that directly compare these paradigms. Comparative metrics will include:

Accuracy: Energy/force prediction MAEs, orbital density errors

Scalability: Performance with system size, qubit count, and model parameters

Generalization: Cross-molecule and out-of-distribution robustness

Computational Resources: Wall-clock time, quantum/classical hardware use, training efficiency

Datasets of focus: QM7, QM9, ANI-1x, MD17.

3. Application Domains
Each paradigm will be evaluated in real-world quantum chemistry scenarios:

Molecular property prediction: HOMO-LUMO gaps, dipole moments, vibrational modes

Reaction pathway modeling: Transition state search using PES predictions

Materials and drug discovery: Ligand binding affinity, conformational sampling, catalyst design

4. Key Experts and Research Groups
Pure Quantum: Aspuru-Guzik (U Toronto), Garnet Chan (Caltech), IBM Quantum, Google Quantum AI

QML: Maria Schuld & Nathan Killoran (Xanadu), Giuseppe Carleo (EPFL), Kristan Temme (IBM)

Classical ML: Klaus-Robert Müller (TU Berlin), Anatole von Lilienfeld (U Vienna), DeepMind, Microsoft Research

Their latest publications, talks, and GitHub repositories will be used as primary technical sources.

5. Temporal Focus
The primary literature corpus will center on work from 2022 to present, including arXiv preprints and conference proceedings (NeurIPS, ICML, ACS, PRX Quantum). Earlier foundational papers (2017–2021) will be referenced to contextualize methods and trace algorithmic evolution.

6. Technical Depth and Implementation
This research will include a hands-on component:

Reproducing or extending open-source implementations (Qiskit, PennyLane, DeepChem)

Running small-scale quantum experiments on IBM Q / IonQ simulators

Benchmarking ML models in PyTorch/TensorFlow on quantum chemistry datasets

Analyzing scaling behavior with increasing molecular complexity

All implementations and evaluations will be documented with clear technical rationale to support reproducibility and transparency.
                                        </div>
                                    </div>
                                    
                                    <div className="action-results">
                                        {isPodcastGenerating && (
                                            <div className="action-status">Generating podcast...</div>
                                        )}
                                        {podcastUrl && (
                                            <div className="action-success">
                                                Podcast generated successfully! 
                                                <a href={podcastUrl} target="_blank" rel="noopener noreferrer" className="result-link">
                                                    Listen to Podcast
                                                </a>
                                            </div>
                                        )}
                                        
                                        {isSharing && (
                                            <div className="action-status">Sharing content...</div>
                                        )}
                                        {shareUrl && (
                                            <div className="action-success">
                                                Content shared successfully! 
                                                <a href={shareUrl} target="_blank" rel="noopener noreferrer" className="result-link">
                                                    View Shared Content
                                                </a>
                                            </div>
                                        )}
                                        
                                        {isPosting && (
                                            <div className="action-status">Posting content...</div>
                                        )}
                                        {postResult && (
                                            <div className="action-success">{postResult}</div>
                                        )}
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

    // -- Main render --
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

export default Query;
