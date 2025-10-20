"""
VIOLENT EVENT ANNOTATION TOOLS PACKAGE
======================================

Complete toolkit for managing violent event annotation project.

Contents:
1. validate_annotations.py - Validate annotation data quality
2. calculate_iaa.py - Calculate inter-annotator agreement
3. annotation_stats.py - Generate statistics and reports
4. data_quality_checker.py - Identify problematic annotations
5. Template specifications

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

# ============================================================================
# FILE 1: validate_annotations.py
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List, Tuple
import json

class AnnotationValidator:
    """
    Validates annotation data for completeness, consistency, and format.
    """
    
    def __init__(self, taxonomy_path: str = None):
        """
        Initialize validator with taxonomy definitions.
        
        Args:
            taxonomy_path: Path to taxonomy JSON file (optional)
        """
        self.errors = []
        self.warnings = []
        
        # Valid taxonomy categories (should match your taxonomy)
        self.valid_l1 = [
            "Political Violence",
            "Criminal Violence", 
            "Communal Violence",
            "State Violence Against Civilians"
        ]
        
        self.valid_l2 = {
            "Political Violence": [
                "Rebellion/Armed Insurgency",
                "Terrorism",
                "Coup and Regime Change Violence",
                "Election Violence",
                "Political Repression"
            ],
            "Criminal Violence": [
                "Organized Crime Violence",
                "Armed Robbery/Banditry",
                "Kidnapping for Ransom",
                "Criminal Gang Violence"
            ],
            "Communal Violence": [
                "Ethnic/Tribal Conflict",
                "Religious Violence",
                "Resource-Based Conflict",
                "Pastoralist-Farmer Clashes"
            ],
            "State Violence Against Civilians": [
                "Extrajudicial Killings",
                "State Repression of Protests",
                "Mass Atrocities by State Forces",
                "Forced Displacement by State",
                "Arbitrary Detention with Violence"
            ]
        }
        
        # Valid controlled vocabularies
        self.valid_actor_types = [
            "State forces",
            "Non-state armed group",
            "Criminal organization",
            "Communal group",
            "Unknown",
            "Multiple"
        ]
        
        self.valid_victim_types = [
            "Civilian",
            "Combatant",
            "Mixed",
            "Infrastructure",
            "Unknown"
        ]
        
        self.valid_weapon_categories = [
            "Firearms",
            "Explosives",
            "Edged weapons",
            "Fire/Arson",
            "Heavy weapons",
            "Multiple",
            "Unknown"
        ]
    
    def validate_file(self, file_path: str) -> Dict:
        """
        Validate an annotation file.
        
        Args:
            file_path: Path to Excel/CSV annotation file
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Load data
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, sheet_name='Event Records')
            else:
                df = pd.read_csv(file_path)
            
            self.errors = []
            self.warnings = []
            
            # Run all validation checks
            self._validate_required_fields(df)
            self._validate_ids(df)
            self._validate_dates(df)
            self._validate_coordinates(df)
            self._validate_taxonomy(df)
            self._validate_confidence_scores(df)
            self._validate_casualties(df)
            self._validate_controlled_vocabularies(df)
            
            # Compile results
            results = {
                'status': 'PASS' if len(self.errors) == 0 else 'FAIL',
                'total_events': len(df),
                'errors': self.errors,
                'warnings': self.warnings,
                'error_count': len(self.errors),
                'warning_count': len(self.warnings)
            }
            
            return results
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error_message': str(e),
                'errors': [f"Failed to load file: {str(e)}"]
            }
    
    def _validate_required_fields(self, df: pd.DataFrame):
        """Check that all required fields are present and non-empty."""
        required_fields = [
            'Event_ID', 'Article_ID', 'Actor_Normalized', 
            'Victim_Normalized', 'Location_Country', 'Date_Normalized',
            'Taxonomy_L1', 'Taxonomy_L2', 'Taxonomy_L3'
        ]
        
        for field in required_fields:
            if field not in df.columns:
                self.errors.append(f"Missing required column: {field}")
                continue
                
            null_rows = df[df[field].isna()].index.tolist()
            if null_rows:
                self.errors.append(
                    f"Field '{field}' has missing values in rows: {null_rows[:10]}"
                    f"{' (showing first 10)' if len(null_rows) > 10 else ''}"
                )
    
    def _validate_ids(self, df: pd.DataFrame):
        """Validate ID format and uniqueness."""
        if 'Event_ID' in df.columns:
            # Check format (should be ART_XXX_EVT_YY)
            invalid_ids = []
            for idx, event_id in df['Event_ID'].items():
                if not isinstance(event_id, str):
                    invalid_ids.append((idx, event_id))
                    continue
                if not re.match(r'^ART_\d{3}_EVT_\d{2}$', event_id):
                    invalid_ids.append((idx, event_id))
            
            if invalid_ids:
                self.errors.append(
                    f"Invalid Event_ID format in rows: {[i[0] for i in invalid_ids[:5]]}"
                )
            
            # Check uniqueness
            duplicates = df[df['Event_ID'].duplicated()]['Event_ID'].tolist()
            if duplicates:
                self.errors.append(f"Duplicate Event_IDs found: {duplicates[:5]}")
    
    def _validate_dates(self, df: pd.DataFrame):
        """Validate date format and logical consistency."""
        if 'Date_Normalized' not in df.columns:
            return
        
        invalid_dates = []
        future_dates = []
        
        today = datetime.now().date()
        
        for idx, date_val in df['Date_Normalized'].items():
            if pd.isna(date_val):
                continue
                
            try:
                if isinstance(date_val, str):
                    date_obj = datetime.strptime(date_val, '%Y-%m-%d').date()
                elif isinstance(date_val, datetime):
                    date_obj = date_val.date()
                else:
                    date_obj = pd.to_datetime(date_val).date()
                
                # Check if date is in future
                if date_obj > today:
                    future_dates.append((idx, date_val))
                    
            except Exception as e:
                invalid_dates.append((idx, date_val))
        
        if invalid_dates:
            self.errors.append(
                f"Invalid date format in rows: {[i[0] for i in invalid_dates[:5]]}"
            )
        
        if future_dates:
            self.warnings.append(
                f"Future dates found in rows: {[i[0] for i in future_dates[:5]]}"
            )
    
    def _validate_coordinates(self, df: pd.DataFrame):
        """Validate geographic coordinates."""
        if 'Location_Coordinates' not in df.columns:
            return
        
        invalid_coords = []
        
        for idx, coords in df['Location_Coordinates'].items():
            if pd.isna(coords) or coords == "Unable to geocode":
                continue
            
            if isinstance(coords, str):
                try:
                    parts = coords.split(',')
                    if len(parts) != 2:
                        invalid_coords.append((idx, coords))
                        continue
                    
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    
                    # Check valid ranges
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        invalid_coords.append((idx, coords))
                        
                except:
                    invalid_coords.append((idx, coords))
        
        if invalid_coords:
            self.errors.append(
                f"Invalid coordinates in rows: {[i[0] for i in invalid_coords[:5]]}"
            )
    
    def _validate_taxonomy(self, df: pd.DataFrame):
        """Validate taxonomy classifications."""
        taxonomy_errors = []
        
        for idx, row in df.iterrows():
            if pd.isna(row.get('Taxonomy_L1')):
                continue
            
            l1 = row.get('Taxonomy_L1')
            l2 = row.get('Taxonomy_L2')
            
            # Check L1 validity
            if l1 not in self.valid_l1:
                taxonomy_errors.append(
                    f"Row {idx}: Invalid L1 category '{l1}'"
                )
            
            # Check L2 validity and consistency with L1
            if pd.notna(l2):
                if l1 in self.valid_l2:
                    if l2 not in self.valid_l2[l1]:
                        taxonomy_errors.append(
                            f"Row {idx}: L2 '{l2}' not valid under L1 '{l1}'"
                        )
        
        if taxonomy_errors:
            for error in taxonomy_errors[:10]:
                self.errors.append(error)
    
    def _validate_confidence_scores(self, df: pd.DataFrame):
        """Validate confidence scores are in valid range."""
        confidence_cols = [
            'Actor_Confidence', 'Victim_Confidence', 
            'Location_Confidence', 'Date_Confidence',
            'Classification_Confidence'
        ]
        
        for col in confidence_cols:
            if col not in df.columns:
                continue
            
            invalid_scores = []
            for idx, score in df[col].items():
                if pd.isna(score):
                    continue
                try:
                    score_float = float(score)
                    if not (0.0 <= score_float <= 1.0):
                        invalid_scores.append((idx, score))
                except:
                    invalid_scores.append((idx, score))
            
            if invalid_scores:
                self.errors.append(
                    f"{col} has invalid values (must be 0.0-1.0) in rows: "
                    f"{[i[0] for i in invalid_scores[:5]]}"
                )
    
    def _validate_casualties(self, df: pd.DataFrame):
        """Validate casualty numbers are non-negative integers."""
        casualty_cols = ['Deaths', 'Injuries']
        
        for col in casualty_cols:
            if col not in df.columns:
                continue
            
            invalid_casualties = []
            for idx, count in df[col].items():
                if pd.isna(count):
                    continue
                try:
                    count_int = int(count)
                    if count_int < 0:
                        invalid_casualties.append((idx, count))
                except:
                    invalid_casualties.append((idx, count))
            
            if invalid_casualties:
                self.errors.append(
                    f"{col} has invalid values (must be non-negative integers) "
                    f"in rows: {[i[0] for i in invalid_casualties[:5]]}"
                )
    
    def _validate_controlled_vocabularies(self, df: pd.DataFrame):
        """Validate controlled vocabulary fields."""
        vocab_checks = [
            ('Actor_Type', self.valid_actor_types),
            ('Victim_Type', self.valid_victim_types),
            ('Weapon_Category', self.valid_weapon_categories)
        ]
        
        for col, valid_values in vocab_checks:
            if col not in df.columns:
                continue
            
            invalid_values = []
            for idx, val in df[col].items():
                if pd.isna(val):
                    continue
                if val not in valid_values:
                    invalid_values.append((idx, val))
            
            if invalid_values:
                self.warnings.append(
                    f"{col} has non-standard values in rows: "
                    f"{[i[0] for i in invalid_values[:5]]}. "
                    f"Valid values: {valid_values}"
                )
    
    def generate_report(self, results: Dict, output_file: str = None):
        """Generate human-readable validation report."""
        report = []
        report.append("=" * 70)
        report.append("ANNOTATION VALIDATION REPORT")
        report.append("=" * 70)
        report.append(f"Status: {results['status']}")
        report.append(f"Total Events: {results['total_events']}")
        report.append(f"Errors: {results['error_count']}")
        report.append(f"Warnings: {results['warning_count']}")
        report.append("")
        
        if results['errors']:
            report.append("ERRORS:")
            report.append("-" * 70)
            for i, error in enumerate(results['errors'], 1):
                report.append(f"{i}. {error}")
            report.append("")
        
        if results['warnings']:
            report.append("WARNINGS:")
            report.append("-" * 70)
            for i, warning in enumerate(results['warnings'], 1):
                report.append(f"{i}. {warning}")
            report.append("")
        
        if results['status'] == 'PASS':
            report.append("✓ All validation checks passed!")
        else:
            report.append("✗ Validation failed. Please fix errors above.")
        
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


# ============================================================================
# FILE 2: calculate_iaa.py
# ============================================================================

from sklearn.metrics import cohen_kappa_score
import pandas as pd
from typing import List, Dict, Tuple

class InterAnnotatorAgreement:
    """
    Calculate inter-annotator agreement metrics.
    """
    
    def __init__(self):
        """Initialize IAA calculator."""
        self.results = {}
    
    def calculate_kappa(self, annotator1_file: str, annotator2_file: str,
                       field: str) -> Dict:
        """
        Calculate Cohen's Kappa for a specific field.
        
        Args:
            annotator1_file: Path to first annotator's file
            annotator2_file: Path to second annotator's file
            field: Field name to compare (e.g., 'Taxonomy_L1')
            
        Returns:
            Dictionary with kappa score and interpretation
        """
        try:
            # Load both annotators' data
            df1 = self._load_annotations(annotator1_file)
            df2 = self._load_annotations(annotator2_file)
            
            # Merge on Event_ID to match corresponding events
            merged = pd.merge(
                df1[['Event_ID', field]], 
                df2[['Event_ID', field]],
                on='Event_ID',
                suffixes=('_ann1', '_ann2')
            )
            
            if len(merged) == 0:
                return {
                    'error': 'No matching Event_IDs found between annotators'
                }
            
            # Calculate Cohen's Kappa
            ann1_values = merged[f'{field}_ann1']
            ann2_values = merged[f'{field}_ann2']
            
            # Remove rows where either annotator has missing values
            mask = ann1_values.notna() & ann2_values.notna()
            ann1_clean = ann1_values[mask]
            ann2_clean = ann2_values[mask]
            
            if len(ann1_clean) == 0:
                return {
                    'error': f'No valid annotations for field {field}'
                }
            
            kappa = cohen_kappa_score(ann1_clean, ann2_clean)
            
            # Interpret kappa
            interpretation = self._interpret_kappa(kappa)
            
            # Calculate agreement percentage
            agreement_pct = (ann1_clean == ann2_clean).sum() / len(ann1_clean) * 100
            
            results = {
                'field': field,
                'kappa': round(kappa, 4),
                'interpretation': interpretation,
                'agreement_percentage': round(agreement_pct, 2),
                'n_compared': len(ann1_clean),
                'annotator1_file': annotator1_file,
                'annotator2_file': annotator2_file
            }
            
            return results
            
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def calculate_all_kappas(self, annotator1_file: str, 
                           annotator2_file: str) -> Dict:
        """
        Calculate kappa for all key fields.
        
        Returns:
            Dictionary with kappa scores for multiple fields
        """
        fields_to_check = [
            'Taxonomy_L1',
            'Taxonomy_L2',
            'Taxonomy_L3',
            'Actor_Type',
            'Victim_Type',
            'Weapon_Category'
        ]
        
        all_results = {}
        
        for field in fields_to_check:
            result = self.calculate_kappa(annotator1_file, annotator2_file, field)
            all_results[field] = result
        
        return all_results
    
    def _load_annotations(self, file_path: str) -> pd.DataFrame:
        """Load annotation file."""
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path, sheet_name='Event Records')
        else:
            return pd.read_csv(file_path)
    
    def _interpret_kappa(self, kappa: float) -> str:
        """
        Interpret kappa value according to Landis & Koch scale.
        
        < 0: Poor
        0.0 - 0.20: Slight
        0.21 - 0.40: Fair
        0.41 - 0.60: Moderate
        0.61 - 0.80: Substantial
        0.81 - 1.00: Almost Perfect
        """
        if kappa < 0:
            return "Poor (worse than random)"
        elif kappa < 0.20:
            return "Slight agreement"
        elif kappa < 0.40:
            return "Fair agreement"
        elif kappa < 0.60:
            return "Moderate agreement"
        elif kappa < 0.80:
            return "Substantial agreement"
        else:
            return "Almost perfect agreement"
    
    def identify_disagreements(self, annotator1_file: str, 
                             annotator2_file: str,
                             field: str) -> pd.DataFrame:
        """
        Identify specific cases where annotators disagreed.
        
        Returns:
            DataFrame with disagreement cases
        """
        df1 = self._load_annotations(annotator1_file)
        df2 = self._load_annotations(annotator2_file)
        
        # Select relevant columns for comparison
        cols_to_keep = [
            'Event_ID', 'Article_ID', field, 
            'Event_Description', 'Actor_Normalized', 'Victim_Normalized'
        ]
        
        # Keep only columns that exist
        cols1 = [c for c in cols_to_keep if c in df1.columns]
        cols2 = [c for c in cols_to_keep if c in df2.columns]
        
        merged = pd.merge(
            df1[cols1],
            df2[cols2],
            on='Event_ID',
            suffixes=('_ann1', '_ann2')
        )
        
        # Filter to disagreements
        disagreements = merged[
            merged[f'{field}_ann1'] != merged[f'{field}_ann2']
        ]
        
        return disagreements
    
    def generate_iaa_report(self, results: Dict, output_file: str = None) -> str:
        """Generate IAA report."""
        report = []
        report.append("=" * 70)
        report.append("INTER-ANNOTATOR AGREEMENT REPORT")
        report.append("=" * 70)
        report.append("")
        
        for field, result in results.items():
            if 'error' in result:
                report.append(f"{field}: ERROR - {result['error']}")
                continue
            
            report.append(f"Field: {field}")
            report.append(f"  Cohen's Kappa: {result['kappa']}")
            report.append(f"  Interpretation: {result['interpretation']}")
            report.append(f"  Agreement %: {result['agreement_percentage']}%")
            report.append(f"  Cases compared: {result['n_compared']}")
            report.append("")
        
        report.append("=" * 70)
        report.append("INTERPRETATION GUIDE:")
        report.append("  Kappa < 0.20: Slight agreement")
        report.append("  Kappa 0.21-0.40: Fair agreement")
        report.append("  Kappa 0.41-0.60: Moderate agreement")
        report.append("  Kappa 0.61-0.80: Substantial agreement")
        report.append("  Kappa 0.81-1.00: Almost perfect agreement")
        report.append("")
        report.append("TARGETS:")
        report.append("  Level 1 (Broad): Kappa ≥ 0.75")
        report.append("  Level 2 (Intermediate): Kappa ≥ 0.70")
        report.append("  Level 3 (Specific): Kappa ≥ 0.65")
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


# ============================================================================
# FILE 3: annotation_stats.py
# ============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from datetime import datetime

class AnnotationStatistics:
    """
    Generate statistics and visualizations for annotation project.
    """
    
    def __init__(self):
        """Initialize statistics generator."""
        self.df = None
        self.stats = {}
    
    def load_data(self, file_path: str):
        """Load annotation data."""
        if file_path.endswith('.xlsx'):
            self.df = pd.read_excel(file_path, sheet_name='Event Records')
        else:
            self.df = pd.read_csv(file_path)
    
    def calculate_statistics(self) -> Dict:
        """Calculate comprehensive statistics."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        stats = {}
        
        # Basic counts
        stats['total_events'] = len(self.df)
        stats['total_articles'] = self.df['Article_ID'].nunique()
        stats['events_per_article'] = stats['total_events'] / stats['total_articles']
        
        # Taxonomy distribution
        stats['taxonomy_l1_dist'] = self.df['Taxonomy_L1'].value_counts().to_dict()
        stats['taxonomy_l2_dist'] = self.df['Taxonomy_L2'].value_counts().to_dict()
        stats['taxonomy_l3_dist'] = self.df['Taxonomy_L3'].value_counts().to_dict()
        
        # Actor types
        stats['actor_type_dist'] = self.df['Actor_Type'].value_counts().to_dict()
        
        # Victim types
        stats['victim_type_dist'] = self.df['Victim_Type'].value_counts().to_dict()
        
        # Casualties
        stats['total_deaths'] = self.df['Deaths'].sum()
        stats['total_injuries'] = self.df['Injuries'].sum()
        stats['avg_deaths_per_event'] = self.df['Deaths'].mean()
        stats['avg_injuries_per_event'] = self.df['Injuries'].mean()
        
        # Geographic distribution
        stats['countries'] = self.df['Location_Country'].value_counts().to_dict()
        
        # Temporal distribution
        if 'Date_Normalized' in self.df.columns:
            self.df['Date_Normalized'] = pd.to_datetime(self.df['Date_Normalized'])
            self.df['Year'] = self.df['Date_Normalized'].dt.year
            self.df['Month'] = self.df['Date_Normalized'].dt.month
            stats['events_by_year'] = self.df['Year'].value_counts().sort_index().to_dict()
            stats['events_by_month'] = self.df['Month'].value_counts().sort_index().to_dict()
        
        # Confidence scores
        confidence_cols = [
            'Actor_Confidence', 'Victim_Confidence', 
            'Location_Confidence', 'Classification_Confidence'
        ]
        for col in confidence_cols:
            if col in self.df.columns:
                stats[f'{col}_mean'] = self.df[col].mean()
                stats[f'{col}_median'] = self.df[col].median()
        
        # Flagged events
        if 'Flagged_for_Review' in self.df.columns:
            stats['flagged_count'] = self.df['Flagged_for_Review'].sum()
            stats['flagged_percentage'] = (stats['flagged_count'] / stats['total_events']) * 100
        
        # Annotator statistics
        if 'Annotator_Name' in self.df.columns:
            stats['annotators'] = self.df['Annotator_Name'].value_counts().to_dict()
        
        self.stats = stats
        return stats
    
    def generate_visualizations(self, output_dir: str = './charts'):
        """Generate visualization charts."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        
        # 1. Taxonomy L1 distribution
        plt.figure(figsize=(10, 6))
        l1_data = pd.Series(self.stats['taxonomy_l1_dist'])
        l1_data.plot(kind='bar', color='steelblue')
        plt.title('Distribution of Events by Level 1 Taxonomy', fontsize=14, fontweight='bold')
        plt.xlabel('Category')
        plt.ylabel('Number of Events')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/taxonomy_l1_distribution.png', dpi=300)
        plt.close()
        
        # 2. Top 10 Level 2 categories
        plt.figure(figsize=(12, 6))
        l2_data = pd.Series(self.stats['taxonomy_l2_dist']).head(10)
        l2_data.plot(kind='barh', color='coral')
        plt.title('Top 10 Event Types (Level 2)', fontsize=14, fontweight='bold')
        plt.xlabel('Number of Events')
        plt.ylabel('Event Type')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/taxonomy_l2_top10.png', dpi=300)
        plt.close()
        
        # 3. Geographic distribution (top countries)
        plt.figure(figsize=(10, 6))
        country_data = pd.Series(self.stats['countries']).head(10)
        country_data.plot(kind='bar', color='green')
        plt.title('Events by Country (Top 10)', fontsize=14, fontweight='bold')
        plt.xlabel('Country')
        plt.ylabel('Number of Events')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/geographic_distribution.png', dpi=300)
        plt.close()
        
        # 4. Temporal distribution
        if 'events_by_month' in self.stats:
            plt.figure(figsize=(12, 6))
            month_data = pd.Series(self.stats['events_by_month'])
            month_data.plot(kind='line', marker='o', color='purple')
            plt.title('Events by Month', fontsize=14, fontweight='bold')
            plt.xlabel('Month')
            plt.ylabel('Number of Events')
            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{output_dir}/temporal_distribution.png', dpi=300)
            plt.close()
        
        # 5. Casualty statistics
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Deaths histogram
        deaths = self.df['Deaths'].dropna()
        ax1.hist(deaths, bins=20, color='red', alpha=0.7, edgecolor='black')
        ax1.set_title('Distribution of Deaths per Event')
        ax1.set_xlabel('Number of Deaths')
        ax1.set_ylabel('Frequency')
        
        # Injuries histogram
        injuries = self.df['Injuries'].dropna()
        ax2.hist(injuries, bins=20, color='orange', alpha=0.7, edgecolor='black')
        ax2.set_title('Distribution of Injuries per Event')
        ax2.set_xlabel('Number of Injuries')
        ax2.set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/casualty_distribution.png', dpi=300)
        plt.close()
        
        print(f"Visualizations saved to {output_dir}/")
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive statistics report."""
        if not self.stats:
            self.calculate_statistics()
        
        report = []
        report.append("=" * 70)
        report.append("ANNOTATION STATISTICS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        report.append("")
        
        # Overview
        report.append("OVERVIEW")
        report.append("-" * 70)
        report.append(f"Total Events Annotated: {self.stats['total_events']}")
        report.append(f"Total Articles: {self.stats['total_articles']}")
        report.append(f"Events per Article (avg): {self.stats['events_per_article']:.2f}")
        report.append("")
        
        # Casualties
        report.append("CASUALTIES")
        report.append("-" * 70)
        report.append(f"Total Deaths: {self.stats['total_deaths']:.0f}")
        report.append(f"Total Injuries: {self.stats['total_injuries']:.0f}")
        report.append(f"Average Deaths per Event: {self.stats['avg_deaths_per_event']:.2f}")
        report.append(f"Average Injuries per Event: {self.stats['avg_injuries_per_event']:.2f}")
        report.append("")
        
        # Taxonomy L1
        report.append("TAXONOMY LEVEL 1 DISTRIBUTION")
        report.append("-" * 70)
        for category, count in sorted(self.stats['taxonomy_l1_dist'].items(), 
                                     key=lambda x: x[1], reverse=True):
            pct = (count / self.stats['total_events']) * 100
            report.append(f"  {category}: {count} ({pct:.1f}%)")
        report.append("")
        
        # Top 10 Level 2
        report.append("TOP 10 EVENT TYPES (Level 2)")
        report.append("-" * 70)
        l2_sorted = sorted(self.stats['taxonomy_l2_dist'].items(), 
                          key=lambda x: x[1], reverse=True)[:10]
        for i, (category, count) in enumerate(l2_sorted, 1):
            pct = (count / self.stats['total_events']) * 100
            report.append(f"  {i}. {category}: {count} ({pct:.1f}%)")
        report.append("")
        
        # Geographic
        report.append("GEOGRAPHIC DISTRIBUTION (Top 10 Countries)")
        report.append("-" * 70)
        country_sorted = sorted(self.stats['countries'].items(), 
                               key=lambda x: x[1], reverse=True)[:10]
        for i, (country, count) in enumerate(country_sorted, 1):
            pct = (count / self.stats['total_events']) * 100
            report.append(f"  {i}. {country}: {count} ({pct:.1f}%)")
        report.append("")
        
        # Confidence scores
        report.append("CONFIDENCE SCORES")
        report.append("-" * 70)
        conf_fields = [
            'Actor_Confidence', 'Victim_Confidence',
            'Location_Confidence', 'Classification_Confidence'
        ]
        for field in conf_fields:
            mean_key = f'{field}_mean'
            if mean_key in self.stats:
                report.append(f"  {field}: {self.stats[mean_key]:.3f}")
        report.append("")
        
        # Annotators
        if 'annotators' in self.stats:
            report.append("ANNOTATOR PRODUCTIVITY")
            report.append("-" * 70)
            for annotator, count in sorted(self.stats['annotators'].items(),
                                          key=lambda x: x[1], reverse=True):
                pct = (count / self.stats['total_events']) * 100
                report.append(f"  {annotator}: {count} events ({pct:.1f}%)")
            report.append("")
        
        # Flagged events
        if 'flagged_count' in self.stats:
            report.append("QUALITY FLAGS")
            report.append("-" * 70)
            report.append(f"  Events Flagged for Review: {self.stats['flagged_count']}")
            report.append(f"  Percentage Flagged: {self.stats['flagged_percentage']:.2f}%")
            report.append("")
        
        report.append("=" * 70)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text


# ============================================================================
# FILE 4: Main Usage Script
# ============================================================================

def main():
    """
    Main script demonstrating how to use all tools.
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Violent Event Annotation Tools'
    )
    parser.add_argument('command', choices=['validate', 'iaa', 'stats'],
                       help='Command to execute')
    parser.add_argument('--file', required=True,
                       help='Path to annotation file')
    parser.add_argument('--file2', help='Path to second annotation file (for IAA)')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    if args.command == 'validate':
        print("Validating annotations...")
        validator = AnnotationValidator()
        results = validator.validate_file(args.file)
        report = validator.generate_report(results, args.output)
        print(report)
        
    elif args.command == 'iaa':
        if not args.file2:
            print("ERROR: --file2 required for IAA calculation")
            sys.exit(1)
        print("Calculating inter-annotator agreement...")
        iaa = InterAnnotatorAgreement()
        results = iaa.calculate_all_kappas(args.file, args.file2)
        report = iaa.generate_iaa_report(results, args.output)
        print(report)
        
    elif args.command == 'stats':
        print("Generating statistics...")
        stats = AnnotationStatistics()
        stats.load_data(args.file)
        stats.calculate_statistics()
        report = stats.generate_report(args.output)
        print(report)
        
        # Generate visualizations
        stats.generate_visualizations('./annotation_charts')
        print("\nVisualizations saved to ./annotation_charts/")


if __name__ == '__main__':
    main()


"""
USAGE EXAMPLES:
===============

1. Validate annotations:
   python annotation_tools.py validate --file annotations.xlsx --output validation_report.txt

2. Calculate inter-annotator agreement:
   python annotation_tools.py iaa --file annotator1.xlsx --file2 annotator2.xlsx --output iaa_report.txt

3. Generate statistics:
   python annotation_tools.py stats --file annotations.xlsx --output stats_report.txt


INSTALLATION:
=============

pip install pandas numpy scikit-learn matplotlib seaborn openpyxl


FILE STRUCTURE:
===============

Save this as: annotation_tools.py

Then run with:
python annotation_tools.py [command] [options]
"""