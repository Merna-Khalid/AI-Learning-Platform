import requests
import json
from typing import Dict, Any, List
from app.config import settings

class CodeExecutionService:
    def __init__(self):
        self.executor_url = getattr(settings, 'CODE_EXECUTOR_URL', 'http://code-executor:8080')
    
    async def test_student_code(self, problem_data: Dict, student_code: str, language: str) -> Dict[str, Any]:
        """Test student code against test cases"""
        test_cases = problem_data.get('test_cases', [])
        results = []
        
        for test_case in test_cases:
            execution_result = await self._execute_code(language, student_code, test_case.get('input', ''))
            
            passed = self._compare_outputs(
                execution_result.get('stdout', ''), 
                test_case.get('expected_output', ''),
                problem_data.get('output_type', 'exact')
            )
            
            results.append({
                'test_case_id': test_case.get('id'),
                'passed': passed,
                'expected': test_case.get('expected_output'),
                'actual': execution_result.get('stdout'),
                'input': test_case.get('input'),
                'execution_result': execution_result
            })
        
        passed_count = sum(1 for r in results if r['passed'])
        total_score = (passed_count / len(results)) * 100 if results else 0
        
        return {
            'score': total_score,
            'total_tests': len(results),
            'passed_tests': passed_count,
            'detailed_results': results
        }
    
    async def _execute_code(self, language: str, code: str, input_data: str = "") -> Dict[str, Any]:
        """Execute code via the code execution service"""
        try:
            payload = {
                'language': language,
                'code': code,
                'input': input_data
            }
            
            response = requests.post(
                f"{self.executor_url}/execute",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            return {'error': f'Execution service error: {str(e)}'}
    
    def _compare_outputs(self, actual: str, expected: str, comparison_type: str) -> bool:
        """Compare outputs based on comparison type"""
        actual_clean = actual.strip()
        expected_clean = expected.strip()
        
        if comparison_type == 'exact':
            return actual_clean == expected_clean
        elif comparison_type == 'numeric':
            try:
                return float(actual_clean) == float(expected_clean)
            except ValueError:
                return actual_clean == expected_clean
        elif comparison_type == 'contains':
            return expected_clean.lower() in actual_clean.lower()
        else:
            return actual_clean == expected_clean