import os
import tempfile
import subprocess
import resource
import signal
import json
from flask import Flask, request, jsonify
from pathlib import Path

app = Flask(__name__)

# Resource limits
MAX_EXECUTION_TIME = 10  # seconds
MEMORY_LIMIT = 256 * 1024 * 1024  # 256MB
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB

class CodeExecutor:
    def __init__(self):
        self.supported_languages = {
            'python': {'extension': 'py', 'command': 'python3'},
            'javascript': {'extension': 'js', 'command': 'node'},
            'java': {'extension': 'java', 'command': 'java'},
            'cpp': {'extension': 'cpp', 'command': 'g++'},
            'go': {'extension': 'go', 'command': 'go run'},
        }
    
    def set_limits(self):
        """Set resource limits for security"""
        resource.setrlimit(resource.RLIMIT_CPU, (MAX_EXECUTION_TIME, MAX_EXECUTION_TIME))
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))
        resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT_SIZE, MAX_OUTPUT_SIZE))
    
    def execute_code(self, language: str, code: str, input_data: str = "") -> dict:
        """Execute code in a secure environment"""
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=f'.{self.supported_languages[language]["extension"]}',
            delete=False,
            dir='/tmp/executions'
        ) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute with timeout and resource limits
            command = self._build_command(language, temp_file)
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=self.set_limits,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(
                    input=input_data, 
                    timeout=MAX_EXECUTION_TIME
                )
                return_code = process.returncode
                
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": return_code,
                    "success": return_code == 0
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                return {"error": "Execution timeout"}
                
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _build_command(self, language: str, file_path: str) -> list:
        """Build execution command based on language"""
        lang_info = self.supported_languages[language]
        
        if language == 'java':
            # Java needs compilation first
            class_name = Path(file_path).stem
            compile_process = subprocess.run(
                ['javac', file_path], 
                capture_output=True, 
                text=True
            )
            if compile_process.returncode != 0:
                raise Exception(f"Compilation failed: {compile_process.stderr}")
            return ['java', '-cp', '/tmp/executions', class_name]
        elif language == 'cpp':
            # C++ needs compilation
            output_file = file_path.replace('.cpp', '.out')
            compile_process = subprocess.run(
                ['g++', file_path, '-o', output_file], 
                capture_output=True, 
                text=True
            )
            if compile_process.returncode != 0:
                raise Exception(f"Compilation failed: {compile_process.stderr}")
            return [output_file]
        else:
            return lang_info['command'].split() + [file_path]

executor = CodeExecutor()

@app.route('/execute', methods=['POST'])
def execute_code():
    """API endpoint for code execution"""
    data = request.json
    
    if not data or 'language' not in data or 'code' not in data:
        return jsonify({"error": "Missing language or code"}), 400
    
    result = executor.execute_code(
        language=data['language'],
        code=data['code'],
        input_data=data.get('input', '')
    )
    
    return jsonify(result)

@app.route('/languages', methods=['GET'])
def get_languages():
    """Get supported languages"""
    return jsonify(list(executor.supported_languages.keys()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)