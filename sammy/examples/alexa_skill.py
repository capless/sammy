import sammy as sm


sam = sm.SAM(Description='Alexa Skill https://developer.amazon.com/alexa-skills-kit')

sam.add_resource(sm.Function(
    name='AlexaSkillFunction',
    CodeUri=sm.S3URI(Bucket='<bucket>',Key='sammytest.zip'),
    Handler='sample.handler',
    Runtime='python3.6',
    Events=[sm.AlexaSkillEvent(name='AlexaSkillEvent')]
))
