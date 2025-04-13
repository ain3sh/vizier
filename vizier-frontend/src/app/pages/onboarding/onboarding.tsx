import React, { useState } from 'react';
import axios from 'axios';
import './onboarding.css';
import { Slider } from '@mui/material';

const OnBoarding: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [profile, setProfile] = useState({
        identity: '',
        archetype: '',
        goals: '',
        experienceLevel: '5'
    });
    const [errors, setErrors] = useState<Record<string, string>>({});

    const handleInputChange = (field: keyof typeof profile, value: string) => {
        setProfile(prev => ({
            ...prev,
            [field]: value
        }));
        
        // Clear error when field is updated
        if (errors[field]) {
            setErrors(prev => {
                const newErrors = {...prev};
                delete newErrors[field];
                return newErrors;
            });
        }
    };

    const validateStep = (step: number): boolean => {
        const newErrors: Record<string, string> = {};
        
        switch (step) {
            case 2:
                if (profile.identity.length < 20) {
                    newErrors.identity = "Please enter at least 20 characters";
                }
                break;
            case 3:
                if (!profile.archetype) {
                    newErrors.archetype = "Please select an archetype";
                }
                break;
            case 4:
                if (profile.goals.length < 20) {
                    newErrors.goals = "Please enter at least 20 characters";
                }
                break;
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validateStep(currentStep) && currentStep < 6) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleSubmit = async () => {
        try {
            await axios.post('/api/profile', profile);
            // Redirect to dashboard or another page after successful submission
            window.location.href = '../main.tsx';
        } catch (error) {
            console.error('Error submitting profile:', error);
            // Handle error (show message to user, etc.)\
            window.location.href = '../main.tsx';
        }
    };

    const getAriaValueText = (value: number) => {
        return `${value}`;
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return (
                    <div className="onboarding-step">
                        <h1>Welcome to Vizier!</h1>
                        <p style={{fontSize: '20px'}}>Let's get started with a few questions to personalize your experience.</p>
                    </div>
                );
            case 2:
                return (
                    <div className="onboarding-step">
                        <h2>Tell us about you!</h2>
                        <textarea
                            rows={4}
                            placeholder="I am a..."
                            value={profile.identity}
                            onChange={(e) => handleInputChange('identity', e.target.value)}
                            className={`onboarding-input ${errors.identity ? 'input-error' : ''}`}
                        />
                        <div className="input-requirements">
                            <span className={profile.identity.length >= 20 ? 'requirement-met' : ''}>
                                Minimum 20 characters
                            </span>
                            <span className="character-count">
                                {profile.identity.length}/20
                            </span>
                        </div>
                        {errors.identity && <div className="error-message">{errors.identity}</div>}
                    </div>
                );
            case 3:
                return (
                    <div className="onboarding-step">
                        <h2>Which of these best describes you?</h2>
                        <div className="archetype-options">
                            {['Researcher', 'Business Professional', 'Student'].map(type => (
                                <div 
                                    key={type}
                                    className={`archetype-option ${profile.archetype === type ? 'selected' : ''}`}
                                    onClick={() => handleInputChange('archetype', type)}
                                >
                                    <h3>{type}</h3>
                                    <p>{getArchetypeDescription(type)}</p>
                                </div>
                            ))}
                        </div>
                        {errors.archetype && <div className="error-message">{errors.archetype}</div>}
                    </div>
                );
            case 4:
                return (
                    <div className="onboarding-step">
                        <h2>What are your goals and expectations?</h2>
                        <textarea
                            rows={4}
                            placeholder="I want to use Vizier to..."
                            value={profile.goals}
                            onChange={(e) => handleInputChange('goals', e.target.value)}
                            className={`onboarding-input ${errors.goals ? 'input-error' : ''}`}
                        />
                        <div className="input-requirements">
                            <span className={profile.goals.length >= 20 ? 'requirement-met' : ''}>
                                Minimum 20 characters
                            </span>
                            <span className="character-count">
                                {profile.goals.length}/20
                            </span>
                        </div>
                        {errors.goals && <div className="error-message">{errors.goals}</div>}
                    </div>
                );
            case 5:
                return (
                    <div className="onboarding-step">
                        <h2>How are familiar are you with LLMs?</h2>
                        <div className="slider-container">
                            <div className="slider-with-labels">
                                <span className="slider-label">0</span>
                                <div className="slider-wrapper">
                                    <Slider
                                        aria-label="Experience Level"
                                        value={parseInt(profile.experienceLevel)}
                                        onChange={(_, newValue) => handleInputChange('experienceLevel', newValue.toString())}
                                        getAriaValueText={getAriaValueText}
                                        valueLabelDisplay="auto"
                                        step={1}
                                        marks
                                        min={0}
                                        max={10}
                                        sx={{
                                            color: 'rgb(0, 168, 76)',
                                            '& .MuiSlider-thumb': {
                                                width: 24,
                                                height: 24,
                                            },
                                            '& .MuiSlider-valueLabel': {
                                                backgroundColor: 'rgb(0, 168, 76)',
                                            }
                                        }}
                                    />
                                </div>
                                <span className="slider-label">10</span>
                            </div>
                            <div className="slider-description">
                                <span>Beginner</span>
                                <span>Expert</span>
                            </div>
                        </div>
                    </div>
                );
            case 6:
                return (
                    <div className="onboarding-step summary-step">
                        <h2>Review:</h2>
                        <div className="profile-summary">
                            <div className="summary-item">
                                <h3>Who you are:</h3>
                                <p>{profile.identity}</p>
                            </div>
                            <div className="summary-item">
                                <h3>Your archetype:</h3>
                                <p>{profile.archetype}</p>
                            </div>
                            <div className="summary-item">
                                <h3>Your goals with Vizier:</h3>
                                <p>{profile.goals}</p>
                            </div>
                            <div className="summary-item">
                                <h3>Your AI experience level:</h3>
                                <p>{profile.experienceLevel} / 10</p>
                            </div>
                        </div>
                        <button 
                            className="submit-button"
                            onClick={handleSubmit}
                        >
                            Confirm & Continue
                        </button>
                    </div>
                );
            default:
                return null;
        }
    };

    // Helper function for archetype descriptions
    const getArchetypeDescription = (type: string) => {
        switch (type) {
            case 'Researcher':
                return 'You focus on deep analysis and discovering new insights.';
            case 'Business Professional':
                return 'You need practical solutions for business challenges.';
            case 'Student':
                return 'You\'re learning and exploring how AI can help with education.';
            default:
                return '';
        }
    };

    // Check if the current step is valid for enabling the next button
    const isNextButtonEnabled = () => {
        switch (currentStep) {
            case 2:
                return profile.identity.length >= 20;
            case 3:
                return !!profile.archetype;
            case 4:
                return profile.goals.length >= 20;
            default:
                return true;
        }
    };

    return (
        <div className="outer-container">
            <div className="onboarding-container">
                <div className="onboarding-progress">
                    <div className="progress-steps">
                        {[1, 2, 3, 4, 5, 6].map(step => (
                            <div 
                                key={step}
                                className={`progress-step ${currentStep >= step ? 'active' : ''} 
                                            ${currentStep === step ? 'current' : ''}`}
                            >
                                {step < 6 ? step : '✓'}
                            </div>
                        ))}
                    </div>
                    <div className="progress-line">
                        <div 
                            className="progress-completed" 
                            style={{ width: `${(currentStep - 1) * 20}%` }}
                        ></div>
                    </div>
                </div>
                
                <div className="onboarding-content">
                    {renderStep()}
                </div>
                
                <div className="navigation-buttons">
                    {currentStep > 1 && (
                        <button 
                            className="nav-button prev-button"
                            onClick={handlePrevious}
                        >
                            Previous
                        </button>
                    )}
                    {currentStep < 6 && (
                        <button 
                            className={`nav-button next-button ${!isNextButtonEnabled() ? 'disabled' : ''}`}
                            onClick={handleNext}
                            disabled={!isNextButtonEnabled()}
                        >
                            Next
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OnBoarding;