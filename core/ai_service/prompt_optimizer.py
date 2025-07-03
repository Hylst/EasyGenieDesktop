"""Prompt Optimizer for AI Service.

This module optimizes prompts based on user context, preferences, and tool-specific
requirements to improve AI response quality and relevance.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .base_service import UserContext


class PromptTemplate(Enum):
    """Predefined prompt templates for different operations."""
    TASK_ANALYSIS = "task_analysis"
    CONTENT_GENERATION = "content_generation"
    TEXT_TRANSFORMATION = "text_transformation"
    SUGGESTION_GENERATION = "suggestion_generation"
    INSIGHT_EXTRACTION = "insight_extraction"
    ROUTINE_OPTIMIZATION = "routine_optimization"
    READING_ASSISTANCE = "reading_assistance"


class OptimizationStrategy(Enum):
    """Prompt optimization strategies."""
    CONTEXT_INJECTION = "context_injection"
    PERSONA_ADAPTATION = "persona_adaptation"
    EXAMPLE_ENHANCEMENT = "example_enhancement"
    CONSTRAINT_SPECIFICATION = "constraint_specification"
    OUTPUT_FORMATTING = "output_formatting"
    CHAIN_OF_THOUGHT = "chain_of_thought"


@dataclass
class PromptOptimizationResult:
    """Result of prompt optimization."""
    original_prompt: str
    optimized_prompt: str
    strategies_applied: List[OptimizationStrategy]
    context_used: List[str]
    confidence_score: float
    estimated_tokens: int
    optimization_notes: List[str]


@dataclass
class ToolPromptConfig:
    """Configuration for tool-specific prompt optimization."""
    tool_name: str
    operation: str
    base_template: str
    required_context: List[str]
    optional_context: List[str]
    output_format: str
    max_tokens: int
    temperature: float
    strategies: List[OptimizationStrategy]


class PromptOptimizer:
    """Optimizes prompts for better AI responses."""
    
    def __init__(self):
        """Initialize the prompt optimizer."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load prompt templates and configurations
        self.templates = self._load_prompt_templates()
        self.tool_configs = self._load_tool_configurations()
        self.optimization_rules = self._load_optimization_rules()
        
        # Performance tracking
        self.optimization_stats = {
            "total_optimizations": 0,
            "strategy_usage": {strategy.value: 0 for strategy in OptimizationStrategy},
            "average_improvement": 0.0,
            "token_efficiency": 0.0
        }
    
    def _load_prompt_templates(self) -> Dict[str, Dict[str, str]]:
        """Load predefined prompt templates.
        
        Returns:
            Dict[str, Dict[str, str]]: Prompt templates by category and operation
        """
        return {
            "task_breaker": {
                "analyze_task": """
You are an expert task analysis assistant. Analyze the following task and break it down into manageable subtasks.

Task: {task_description}

User Context:
- Experience Level: {experience_level}
- Available Time: {available_time}
- Preferred Work Style: {work_style}
- Previous Similar Tasks: {task_history}

Please provide:
1. Task complexity assessment (Simple/Moderate/Complex/Expert)
2. Estimated total time required
3. List of subtasks with individual time estimates
4. Dependencies between subtasks
5. Recommended order of execution
6. Potential challenges and mitigation strategies

Format your response as structured JSON with clear sections for each element.
""",
                "generate_subtasks": """
Break down this task into specific, actionable subtasks:

Main Task: {task_description}

Consider:
- User's skill level: {skill_level}
- Available resources: {resources}
- Time constraints: {time_constraints}
- Success criteria: {success_criteria}

Provide 3-7 subtasks that are:
- Specific and actionable
- Appropriately sized (15-60 minutes each)
- Logically sequenced
- Include clear completion criteria
"""
            },
            "timefocus": {
                "optimize_session": """
You are a productivity coach specializing in focus optimization. Analyze the user's work pattern and suggest improvements.

Current Session Data:
- Task Type: {task_type}
- Planned Duration: {duration}
- User's Focus Pattern: {focus_pattern}
- Time of Day: {time_of_day}
- Energy Level: {energy_level}
- Distractions Present: {distractions}

Provide personalized recommendations for:
1. Optimal session length
2. Break intervals and activities
3. Environment optimization
4. Focus techniques
5. Distraction management strategies
""",
                "analyze_productivity": """
Analyze the user's productivity patterns and provide insights:

Productivity Data:
{productivity_data}

User Preferences:
{user_preferences}

Identify:
1. Peak productivity hours
2. Common distraction patterns
3. Most effective session lengths
4. Improvement opportunities
5. Personalized recommendations
"""
            },
            "priority_grid": {
                "classify_task": """
Classify this task on the Eisenhower Matrix (Urgent/Important grid):

Task: {task_description}
Deadline: {deadline}
Impact: {impact_description}
Context: {context_info}

User's Current Workload:
{current_tasks}

Provide:
1. Urgency level (1-5) with reasoning
2. Importance level (1-5) with reasoning
3. Recommended quadrant placement
4. Suggested action (Do/Schedule/Delegate/Eliminate)
5. Priority score relative to other tasks
""",
                "optimize_workload": """
Analyze and optimize the user's task workload:

Current Tasks:
{task_list}

User Constraints:
- Available hours per day: {daily_hours}
- Energy patterns: {energy_patterns}
- Deadlines: {deadlines}
- Skills/Resources: {capabilities}

Provide workload optimization:
1. Rebalanced priority assignments
2. Suggested task scheduling
3. Delegation opportunities
4. Tasks to eliminate or postpone
5. Stress reduction strategies
"""
            },
            "brain_dump": {
                "organize_thoughts": """
You are a thought organization expert. Help structure and organize these thoughts:

Raw Thoughts:
{raw_content}

User Context:
- Purpose: {purpose}
- Preferred Organization Style: {org_style}
- Target Audience: {audience}
- Follow-up Actions Needed: {actions_needed}

Organize into:
1. Main themes and categories
2. Key insights and ideas
3. Action items and next steps
4. Questions for further exploration
5. Connections between concepts

Provide a clear, structured output that maintains the original meaning while improving clarity.
""",
                "extract_insights": """
Analyze this content and extract key insights:

Content: {content}

Analysis Focus:
- Emotional patterns: {analyze_emotions}
- Recurring themes: {find_themes}
- Decision points: {identify_decisions}
- Learning opportunities: {extract_learning}

Provide:
1. Key insights and patterns
2. Emotional state analysis
3. Recurring themes and topics
4. Actionable recommendations
5. Suggested follow-up activities
"""
            },
            "formalizer": {
                "transform_text": """
Transform this text to match the specified formality and style:

Original Text:
{original_text}

Target Specifications:
- Formality Level: {formality_level}
- Document Type: {document_type}
- Target Audience: {target_audience}
- Tone: {desired_tone}
- Length: {target_length}

Transformation Requirements:
- Preserve original meaning and key points
- Enhance clarity and professionalism
- Adapt vocabulary and structure appropriately
- Maintain logical flow and coherence
- Follow style conventions for the document type

Provide the transformed text with explanations of major changes made.
""",
                "style_analysis": """
Analyze the writing style and suggest improvements:

Text: {text_content}

Analysis Areas:
- Tone and formality
- Clarity and conciseness
- Structure and flow
- Vocabulary appropriateness
- Grammar and mechanics

Provide detailed feedback and specific improvement suggestions.
"""
            },
            "routine_builder": {
                "optimize_routine": """
Optimize this routine based on habit science and user preferences:

Current Routine:
{routine_description}

User Profile:
- Chronotype: {chronotype}
- Energy Patterns: {energy_patterns}
- Goals: {goals}
- Constraints: {constraints}
- Current Habits: {existing_habits}

Apply habit science principles to:
1. Optimize timing based on circadian rhythms
2. Improve habit stacking and cue design
3. Enhance motivation and reward systems
4. Reduce friction and barriers
5. Increase sustainability and adherence

Provide a scientifically-informed, personalized routine optimization.
""",
                "habit_analysis": """
Analyze habit formation potential for this routine:

Routine Steps:
{routine_steps}

Habit Science Assessment:
1. Cue clarity and consistency
2. Routine simplicity and feasibility
3. Reward immediacy and satisfaction
4. Environmental design factors
5. Motivation sustainability

Provide recommendations for improving habit formation success.
"""
            },
            "immersive_reader": {
                "adapt_content": """
Adapt this content for optimal reading comprehension:

Original Content:
{content}

Reader Profile:
- Reading Level: {reading_level}
- Comprehension Goals: {goals}
- Time Available: {time_limit}
- Learning Style: {learning_style}
- Background Knowledge: {background}

Adaptations Needed:
1. Vocabulary simplification (if needed)
2. Sentence structure optimization
3. Key concept highlighting
4. Summary and preview sections
5. Comprehension aids and questions

Provide adapted content that maintains accuracy while improving accessibility.
""",
                "comprehension_analysis": """
Analyze reading comprehension and provide insights:

Reading Session Data:
{session_data}

Text Characteristics:
{text_analysis}

Provide:
1. Comprehension level assessment
2. Reading speed optimization suggestions
3. Focus improvement strategies
4. Content difficulty adjustments
5. Personalized reading recommendations
"""
            }
        }
    
    def _load_tool_configurations(self) -> Dict[str, Dict[str, ToolPromptConfig]]:
        """Load tool-specific prompt configurations.
        
        Returns:
            Dict[str, Dict[str, ToolPromptConfig]]: Tool configurations
        """
        configs = {}
        
        # Task Breaker configurations
        configs["task_breaker"] = {
            "analyze_task": ToolPromptConfig(
                tool_name="task_breaker",
                operation="analyze_task",
                base_template="task_analysis",
                required_context=["task_description", "user_preferences"],
                optional_context=["task_history", "available_time", "resources"],
                output_format="structured_json",
                max_tokens=1000,
                temperature=0.3,
                strategies=[OptimizationStrategy.CONTEXT_INJECTION, OptimizationStrategy.EXAMPLE_ENHANCEMENT]
            ),
            "generate_subtasks": ToolPromptConfig(
                tool_name="task_breaker",
                operation="generate_subtasks",
                base_template="content_generation",
                required_context=["task_description"],
                optional_context=["skill_level", "time_constraints", "success_criteria"],
                output_format="numbered_list",
                max_tokens=800,
                temperature=0.4,
                strategies=[OptimizationStrategy.CONSTRAINT_SPECIFICATION, OptimizationStrategy.OUTPUT_FORMATTING]
            )
        }
        
        # Add configurations for other tools...
        # (Similar structure for timefocus, priority_grid, etc.)
        
        return configs
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load optimization rules and patterns.
        
        Returns:
            Dict[str, Any]: Optimization rules
        """
        return {
            "context_injection_patterns": {
                "user_experience": "Given your {experience_level} experience with {domain}, ",
                "time_constraint": "With {available_time} available, ",
                "preference": "Considering your preference for {preference_type}, ",
                "history": "Based on your previous work with {similar_tasks}, "
            },
            "persona_adaptations": {
                "beginner": "Explain concepts clearly with examples and avoid jargon.",
                "intermediate": "Provide balanced detail with practical applications.",
                "expert": "Focus on advanced insights and nuanced considerations.",
                "visual_learner": "Include visual descriptions and spatial relationships.",
                "analytical": "Provide logical structure and data-driven insights."
            },
            "output_formatting_rules": {
                "structured_json": "Format your response as valid JSON with clear sections.",
                "numbered_list": "Provide a numbered list with clear, actionable items.",
                "bullet_points": "Use bullet points for easy scanning and comprehension.",
                "paragraph_form": "Write in clear, well-structured paragraphs.",
                "table_format": "Present information in a clear table format."
            },
            "constraint_specifications": {
                "time_limit": "Complete this analysis in under {time_limit} minutes.",
                "word_limit": "Keep your response under {word_limit} words.",
                "complexity_limit": "Maintain {complexity_level} complexity level.",
                "audience_constraint": "Write for {target_audience} audience."
            }
        }
    
    async def optimize(
        self,
        original_prompt: str,
        context: UserContext,
        tool_name: str,
        operation: str
    ) -> str:
        """Optimize a prompt based on context and tool requirements.
        
        Args:
            original_prompt: The original prompt to optimize
            context: User context information
            tool_name: Name of the tool making the request
            operation: Specific operation being performed
            
        Returns:
            str: The optimized prompt
        """
        try:
            # Get tool configuration
            tool_config = self._get_tool_config(tool_name, operation)
            
            # Apply optimization strategies
            optimization_result = await self._apply_optimization_strategies(
                original_prompt,
                context,
                tool_config
            )
            
            # Update statistics
            self._update_optimization_stats(optimization_result)
            
            self.logger.debug(
                f"Optimized prompt for {tool_name}.{operation}: "
                f"{len(optimization_result.strategies_applied)} strategies applied"
            )
            
            return optimization_result.optimized_prompt
            
        except Exception as e:
            self.logger.error(f"Error optimizing prompt: {e}")
            return original_prompt  # Fallback to original
    
    def _get_tool_config(self, tool_name: str, operation: str) -> Optional[ToolPromptConfig]:
        """Get configuration for a specific tool and operation.
        
        Args:
            tool_name: Name of the tool
            operation: Operation being performed
            
        Returns:
            Optional[ToolPromptConfig]: Tool configuration if available
        """
        if tool_name in self.tool_configs:
            return self.tool_configs[tool_name].get(operation)
        return None
    
    async def _apply_optimization_strategies(
        self,
        prompt: str,
        context: UserContext,
        config: Optional[ToolPromptConfig]
    ) -> PromptOptimizationResult:
        """Apply optimization strategies to improve the prompt.
        
        Args:
            prompt: Original prompt
            context: User context
            config: Tool configuration
            
        Returns:
            PromptOptimizationResult: Optimization result
        """
        optimized_prompt = prompt
        strategies_applied = []
        context_used = []
        optimization_notes = []
        
        # Strategy 1: Context Injection
        if not config or OptimizationStrategy.CONTEXT_INJECTION in config.strategies:
            optimized_prompt, context_additions = self._inject_context(
                optimized_prompt, context, config
            )
            if context_additions:
                strategies_applied.append(OptimizationStrategy.CONTEXT_INJECTION)
                context_used.extend(context_additions)
                optimization_notes.append(f"Injected {len(context_additions)} context elements")
        
        # Strategy 2: Persona Adaptation
        if not config or OptimizationStrategy.PERSONA_ADAPTATION in config.strategies:
            optimized_prompt, persona_applied = self._adapt_persona(
                optimized_prompt, context
            )
            if persona_applied:
                strategies_applied.append(OptimizationStrategy.PERSONA_ADAPTATION)
                optimization_notes.append(f"Adapted for {persona_applied} persona")
        
        # Strategy 3: Example Enhancement
        if not config or OptimizationStrategy.EXAMPLE_ENHANCEMENT in config.strategies:
            optimized_prompt, examples_added = self._enhance_with_examples(
                optimized_prompt, context, config
            )
            if examples_added:
                strategies_applied.append(OptimizationStrategy.EXAMPLE_ENHANCEMENT)
                optimization_notes.append(f"Added {examples_added} examples")
        
        # Strategy 4: Constraint Specification
        if not config or OptimizationStrategy.CONSTRAINT_SPECIFICATION in config.strategies:
            optimized_prompt, constraints_added = self._specify_constraints(
                optimized_prompt, context, config
            )
            if constraints_added:
                strategies_applied.append(OptimizationStrategy.CONSTRAINT_SPECIFICATION)
                optimization_notes.append(f"Added {constraints_added} constraints")
        
        # Strategy 5: Output Formatting
        if not config or OptimizationStrategy.OUTPUT_FORMATTING in config.strategies:
            optimized_prompt, formatting_applied = self._apply_output_formatting(
                optimized_prompt, config
            )
            if formatting_applied:
                strategies_applied.append(OptimizationStrategy.OUTPUT_FORMATTING)
                optimization_notes.append(f"Applied {formatting_applied} formatting")
        
        # Strategy 6: Chain of Thought
        if not config or OptimizationStrategy.CHAIN_OF_THOUGHT in config.strategies:
            optimized_prompt, cot_applied = self._add_chain_of_thought(
                optimized_prompt, context, config
            )
            if cot_applied:
                strategies_applied.append(OptimizationStrategy.CHAIN_OF_THOUGHT)
                optimization_notes.append("Added chain-of-thought reasoning")
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            prompt, optimized_prompt, strategies_applied
        )
        
        # Estimate token usage
        estimated_tokens = self._estimate_tokens(optimized_prompt)
        
        return PromptOptimizationResult(
            original_prompt=prompt,
            optimized_prompt=optimized_prompt,
            strategies_applied=strategies_applied,
            context_used=context_used,
            confidence_score=confidence_score,
            estimated_tokens=estimated_tokens,
            optimization_notes=optimization_notes
        )
    
    def _inject_context(
        self,
        prompt: str,
        context: UserContext,
        config: Optional[ToolPromptConfig]
    ) -> Tuple[str, List[str]]:
        """Inject relevant context into the prompt.
        
        Args:
            prompt: Current prompt
            context: User context
            config: Tool configuration
            
        Returns:
            Tuple[str, List[str]]: Updated prompt and list of context additions
        """
        context_additions = []
        updated_prompt = prompt
        
        # Add user experience level
        if "experience_level" in context.preferences:
            experience = context.preferences["experience_level"]
            context_prefix = self.optimization_rules["context_injection_patterns"]["user_experience"]
            updated_prompt = context_prefix.format(
                experience_level=experience,
                domain=config.tool_name if config else "this area"
            ) + updated_prompt
            context_additions.append("experience_level")
        
        # Add time constraints
        if "available_time" in context.current_session:
            time_available = context.current_session["available_time"]
            time_prefix = self.optimization_rules["context_injection_patterns"]["time_constraint"]
            updated_prompt = time_prefix.format(available_time=time_available) + updated_prompt
            context_additions.append("time_constraint")
        
        # Add relevant history
        if context.history:
            recent_tasks = [h for h in context.history[-5:] if h.get("tool_name") == config.tool_name if config else True]
            if recent_tasks:
                history_prefix = self.optimization_rules["context_injection_patterns"]["history"]
                similar_tasks = ", ".join([task.get("description", "similar task") for task in recent_tasks[:3]])
                updated_prompt = history_prefix.format(similar_tasks=similar_tasks) + updated_prompt
                context_additions.append("task_history")
        
        return updated_prompt, context_additions
    
    def _adapt_persona(
        self,
        prompt: str,
        context: UserContext
    ) -> Tuple[str, Optional[str]]:
        """Adapt prompt for user's persona and learning style.
        
        Args:
            prompt: Current prompt
            context: User context
            
        Returns:
            Tuple[str, Optional[str]]: Updated prompt and persona type applied
        """
        # Determine user persona
        experience_level = context.preferences.get("experience_level", "intermediate")
        learning_style = context.preferences.get("learning_style", "analytical")
        
        persona_instruction = ""
        persona_type = None
        
        # Apply experience-based adaptation
        if experience_level in self.optimization_rules["persona_adaptations"]:
            persona_instruction += self.optimization_rules["persona_adaptations"][experience_level]
            persona_type = experience_level
        
        # Apply learning style adaptation
        if learning_style in self.optimization_rules["persona_adaptations"]:
            if persona_instruction:
                persona_instruction += " "
            persona_instruction += self.optimization_rules["persona_adaptations"][learning_style]
            persona_type = f"{persona_type}_{learning_style}" if persona_type else learning_style
        
        if persona_instruction:
            updated_prompt = f"{prompt}\n\nAdditional Instructions: {persona_instruction}"
            return updated_prompt, persona_type
        
        return prompt, None
    
    def _enhance_with_examples(
        self,
        prompt: str,
        context: UserContext,
        config: Optional[ToolPromptConfig]
    ) -> Tuple[str, int]:
        """Enhance prompt with relevant examples.
        
        Args:
            prompt: Current prompt
            context: User context
            config: Tool configuration
            
        Returns:
            Tuple[str, int]: Updated prompt and number of examples added
        """
        examples_added = 0
        
        # Add examples based on user history
        if context.history and config:
            relevant_examples = [
                h for h in context.history
                if h.get("tool_name") == config.tool_name and h.get("success_rating", 0) >= 4
            ][-3:]  # Last 3 successful examples
            
            if relevant_examples:
                example_text = "\n\nExamples from your previous successful sessions:\n"
                for i, example in enumerate(relevant_examples, 1):
                    example_text += f"{i}. {example.get('description', 'Previous task')}: {example.get('outcome', 'Successful completion')}\n"
                
                prompt += example_text
                examples_added = len(relevant_examples)
        
        return prompt, examples_added
    
    def _specify_constraints(
        self,
        prompt: str,
        context: UserContext,
        config: Optional[ToolPromptConfig]
    ) -> Tuple[str, int]:
        """Add specific constraints to the prompt.
        
        Args:
            prompt: Current prompt
            context: User context
            config: Tool configuration
            
        Returns:
            Tuple[str, int]: Updated prompt and number of constraints added
        """
        constraints_added = 0
        constraint_text = ""
        
        # Time constraints
        if "time_limit" in context.current_session:
            time_limit = context.current_session["time_limit"]
            constraint_text += self.optimization_rules["constraint_specifications"]["time_limit"].format(
                time_limit=time_limit
            ) + " "
            constraints_added += 1
        
        # Complexity constraints
        if "complexity_preference" in context.preferences:
            complexity = context.preferences["complexity_preference"]
            constraint_text += self.optimization_rules["constraint_specifications"]["complexity_limit"].format(
                complexity_level=complexity
            ) + " "
            constraints_added += 1
        
        # Token/length constraints from config
        if config and config.max_tokens:
            word_limit = config.max_tokens * 0.75  # Rough conversion
            constraint_text += self.optimization_rules["constraint_specifications"]["word_limit"].format(
                word_limit=int(word_limit)
            ) + " "
            constraints_added += 1
        
        if constraint_text:
            prompt += f"\n\nConstraints: {constraint_text.strip()}"
        
        return prompt, constraints_added
    
    def _apply_output_formatting(
        self,
        prompt: str,
        config: Optional[ToolPromptConfig]
    ) -> Tuple[str, Optional[str]]:
        """Apply output formatting instructions.
        
        Args:
            prompt: Current prompt
            config: Tool configuration
            
        Returns:
            Tuple[str, Optional[str]]: Updated prompt and formatting type applied
        """
        if not config or not config.output_format:
            return prompt, None
        
        format_instruction = self.optimization_rules["output_formatting_rules"].get(
            config.output_format
        )
        
        if format_instruction:
            prompt += f"\n\nOutput Format: {format_instruction}"
            return prompt, config.output_format
        
        return prompt, None
    
    def _add_chain_of_thought(
        self,
        prompt: str,
        context: UserContext,
        config: Optional[ToolPromptConfig]
    ) -> Tuple[str, bool]:
        """Add chain-of-thought reasoning instructions.
        
        Args:
            prompt: Current prompt
            context: User context
            config: Tool configuration
            
        Returns:
            Tuple[str, bool]: Updated prompt and whether CoT was applied
        """
        # Apply CoT for complex operations or when user prefers detailed explanations
        should_apply_cot = (
            context.preferences.get("explanation_detail", "medium") in ["high", "detailed"] or
            (config and "complex" in config.operation.lower()) or
            context.preferences.get("learning_style") == "analytical"
        )
        
        if should_apply_cot:
            cot_instruction = (
                "\n\nPlease think through this step-by-step, showing your reasoning process. "
                "Explain your thought process and the logic behind your recommendations."
            )
            prompt += cot_instruction
            return prompt, True
        
        return prompt, False
    
    def _calculate_confidence_score(
        self,
        original_prompt: str,
        optimized_prompt: str,
        strategies_applied: List[OptimizationStrategy]
    ) -> float:
        """Calculate confidence score for the optimization.
        
        Args:
            original_prompt: Original prompt
            optimized_prompt: Optimized prompt
            strategies_applied: List of applied strategies
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        base_score = 0.5
        
        # Bonus for each strategy applied
        strategy_bonus = len(strategies_applied) * 0.1
        
        # Bonus for prompt length increase (more context usually better)
        length_ratio = len(optimized_prompt) / len(original_prompt) if original_prompt else 1
        length_bonus = min(0.2, (length_ratio - 1) * 0.1)
        
        # Bonus for specific high-value strategies
        high_value_strategies = [
            OptimizationStrategy.CONTEXT_INJECTION,
            OptimizationStrategy.PERSONA_ADAPTATION,
            OptimizationStrategy.CHAIN_OF_THOUGHT
        ]
        high_value_bonus = sum(0.05 for strategy in strategies_applied if strategy in high_value_strategies)
        
        confidence = base_score + strategy_bonus + length_bonus + high_value_bonus
        return min(1.0, confidence)
    
    def _estimate_tokens(self, prompt: str) -> int:
        """Estimate token count for a prompt.
        
        Args:
            prompt: The prompt text
            
        Returns:
            int: Estimated token count
        """
        # Rough estimation: ~4 characters per token for English text
        return len(prompt) // 4
    
    def _update_optimization_stats(self, result: PromptOptimizationResult):
        """Update optimization statistics.
        
        Args:
            result: Optimization result
        """
        self.optimization_stats["total_optimizations"] += 1
        
        for strategy in result.strategies_applied:
            self.optimization_stats["strategy_usage"][strategy.value] += 1
        
        # Update average improvement (based on confidence score)
        current_avg = self.optimization_stats["average_improvement"]
        total_opts = self.optimization_stats["total_optimizations"]
        new_avg = ((current_avg * (total_opts - 1)) + result.confidence_score) / total_opts
        self.optimization_stats["average_improvement"] = new_avg
        
        # Update token efficiency
        original_tokens = self._estimate_tokens(result.original_prompt)
        efficiency = result.confidence_score / (result.estimated_tokens / original_tokens) if original_tokens > 0 else 0
        current_efficiency = self.optimization_stats["token_efficiency"]
        new_efficiency = ((current_efficiency * (total_opts - 1)) + efficiency) / total_opts
        self.optimization_stats["token_efficiency"] = new_efficiency
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics.
        
        Returns:
            Dict[str, Any]: Optimization statistics
        """
        return self.optimization_stats.copy()
    
    def reset_stats(self):
        """Reset optimization statistics."""
        self.optimization_stats = {
            "total_optimizations": 0,
            "strategy_usage": {strategy.value: 0 for strategy in OptimizationStrategy},
            "average_improvement": 0.0,
            "token_efficiency": 0.0
        }
        self.logger.info("Optimization statistics reset")