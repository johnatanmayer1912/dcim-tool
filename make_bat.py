import os
import re

with open(r'build_scripts\build_v6_9_1.bat', 'r') as f:
    content = f.read()

content = content.replace('v6.9.1', 'v6.9.22')

new_features = '''echo  Key Features in v6.9.22:
echo  1. [P0] Jinja2 TemplateSyntaxError Application Fail-to-Start fix
echo  2. Added standards and templates to EXE build
echo  3. Plugin Manifest updated to 13 plugins'''

content = re.sub(r'echo  Key Features.*?echo ==', new_features + '\necho ==', content, flags=re.DOTALL)

content = content.replace(
    'xcopy /E /I /Y "policies" "%DIST_NAME%\\policies" >nul 2>&1',
    'xcopy /E /I /Y "policies" "%DIST_NAME%\\policies" >nul 2>&1\nxcopy /E /I /Y "standards" "%DIST_NAME%\\standards" >nul 2>&1\nxcopy /E /I /Y "templates" "%DIST_NAME%\\templates" >nul 2>&1'
)

with open(r'build_scripts\build_v6_9_2.bat', 'w') as f:
    f.write(content)

print('Build bat file created successfully.')
