import os
import pytest
from unittest.mock import MagicMock
from app.inspector.routes import _parse_eml_detail, _clean_placeholders

def test_placeholder_cleaning():
    text = "Hello {{.FirstName}}, welcome to {{company_name}}. Click here: {{.URL}}"
    cleaned = _clean_placeholders(text)
    assert "{{.FirstName}}" not in cleaned
    assert "{{company_name}}" not in cleaned
    assert "{{.URL}}" not in cleaned
    assert "Valued" in cleaned
    assert "Our Company" in cleaned
    assert "https://example.com/secure-redirect-gateway" in cleaned

@pytest.fixture
def mock_app_context(app):
    with app.app_context():
        yield

def test_all_examples_parse(app):
    """Verify that every .eml in examples/ can be parsed by the inspector logic."""
    from app.inspector.routes import _get_eml_body
    from flask_login import current_user
    
    examples_dir = 'examples'
    eml_files = []
    for root, dirs, files in os.walk(examples_dir):
        for file in files:
            if file.endswith('.eml'):
                eml_files.append(os.path.join(root, file))
    
    assert len(eml_files) > 0
    
    with app.app_context():
        # We need to mock current_app.s3_client and current_app.config['S3_BUCKET']
        app.s3_client = MagicMock()
        app.config['S3_BUCKET'] = 'test-bucket'
        
        # Mock flask_login.current_user
        mock_user = MagicMock()
        mock_user.role = 'admin'
        mock_user.is_admin = True
        
        from unittest.mock import patch
        with patch('app.inspector.routes.current_user', mock_user):
            for eml_path in eml_files:
                with open(eml_path, 'rb') as f:
                    content = f.read()
                
                # Mock the S3 download for this specific file
                app.s3_client.get_object.return_value = {
                    'Body': MagicMock(read=MagicMock(return_value=content))
                }
                
                # The key passed to _parse_eml_detail is usually 'eml-samples/filename.eml'
                filename = os.path.basename(eml_path)
                key = f"eml-samples/{filename}"
                
                try:
                    result = _parse_eml_detail(key)
                
                    # Basic assertions on the result structure
                    assert 'summary' in result
                    assert 'headers' in result
                    assert 'textBody' in result
                    assert 'htmlBody' in result
                    assert 'links' in result
                    assert 'attachments' in result
                    
                    # Verify placeholders are cleaned in the parsed result
                    for link in result['links']:
                        assert '{{.URL}}' not in link
                    
                    assert '{{.FirstName}}' not in result['summary']['subject']
                    assert '{{.FirstName}}' not in result['textBody']
                    assert '{{.FirstName}}' not in result['htmlBody']
                
                except Exception as e:
                    pytest.fail(f"Failed to parse {eml_path}: {str(e)}")
