"""
Demo Script for Class Presentation
Pre-scripted conversation between Alex (Agent) and Ali (Customer)
This ensures smooth demonstration even if API quota is hit
"""

# Demo conversation script - optimized for presentation
DEMO_SCRIPT = {
    # Greeting phase
    "hi": "Hey Ali! This is Alex from Digital Lab. Thanks so much for reaching out! I'm here to help you take your business to the next level. What brings you to us today?",
    
    "hello": "Hey there! Alex from Digital Lab here. Super excited to chat with you! We help businesses grow through amazing digital marketing. What's your biggest challenge right now?",
    
    # Service inquiry phase
    "what services": "Great question! We specialize in everything digital - Video Editing that tells your story, eye-catching Graphic Design, Social Media Marketing that actually converts, Ads Management to maximize your ROI, SEO to get you found on Google, professional Copywriting, and custom Web Development. Which of these sounds most exciting to you?",
    
    "services do you offer": "Awesome! We're a full-service digital marketing agency. Think of us as your one-stop shop for Video Editing, Graphic Design, Social Media Marketing, paid Ads Management, SEO, Copywriting, and Web Development. We basically handle everything you need to dominate online! What area interests you most?",
    
    "tell me about": "Absolutely! We offer a complete digital marketing suite. Our specialties include creating scroll-stopping videos, designs that convert, social media campaigns that engage, search engine optimization to boost your rankings, and websites that actually make sales. What's your business about?",
    
    # SEO specific
    "seo": "Ooh, SEO! Smart choice. We help businesses like yours rank #1 on Google for the keywords that actually matter. Imagine customers finding YOU instead of your competitors. We do keyword research, on-page optimization, link building - the whole package. Most clients see results in 60-90 days. What industry are you in?",
    
    "search engine": "Perfect! SEO is our bread and butter. We've helped dozens of businesses go from page 10 to page 1 on Google. The best part? Once you rank, you get FREE traffic every single day. No more paying for ads! We'd love to run a quick audit on your site. Sound good?",
    
    # Social media specific  
    "social media": "Yes! Social media is HUGE right now. We create content that stops the scroll, run targeted campaigns, and turn followers into paying customers. Instagram, Facebook, TikTok, LinkedIn - we've got you covered. The secret? Understanding your audience psychology. What platform are you most active on?",
    
    "instagram": "Instagram is fire for business right now! We create Reels that go viral, Stories that convert, and ads that bring in customers while you sleep. Our clients typically see 3-5x ROI. Are you currently posting on Instagram or starting fresh?",
    
    # Web development specific
    "website": "Oh man, websites are our THING! We build fast, beautiful, mobile-friendly sites that actually make sales. Not those boring template sites - custom designs that reflect YOUR brand. Plus, we optimize for conversions so visitors become customers. Do you have a site currently or starting new?",
    
    "web development": "Perfect timing! A killer website is your 24/7 salesperson. We design custom sites with smooth user experience, fast loading, and most importantly - they convert visitors into leads. We can have you live in 2-3 weeks typically. What kind of business do you run?",
    
    # Video editing specific
    "video": "Video is the FUTURE! We edit everything from YouTube content to short-form Reels and TikToks. Professional cuts, engaging transitions, captions, sound design - all of it. Videos get 10x more engagement than images. Are you creating content already or want to start?",
    
    "video editing": "Love it! Video content gets crazy engagement. We handle the entire editing process - you send us raw footage, we send back something that looks like a Netflix production. Our turnaround is usually 3-5 days. What type of videos are you thinking?",
    
    # Pricing phase
    "how much": "Great question! Our packages start around $500-$2000 depending on what you need. But here's the thing - every business is unique, so I'd rather give you an exact quote tailored to YOUR goals. How about we hop on a quick 15-minute call? I can show you exactly what we'd do for you. Does tomorrow work?",
    
    "cost": "Investment varies based on scope, but most clients see positive ROI within 60-90 days. We have packages from $500 to $5000+. The real question is - what's getting customers worth to you? Let's schedule a free consultation where I can build you a custom proposal. Sound good?",
    
    "price": "Pricing depends on your specific needs, but think of it as an investment, not an expense. Most packages range $750-$3000. I'd love to understand your goals first, then give you an exact quote with expected ROI. Want to book a quick strategy call? Takes 15 minutes, no pressure!",
    
    "expensive": "I totally get it! But here's the thing - quality marketing pays for itself. Our average client makes back their investment in the first month. Think of it this way: would you rather save $500 now or make $10,000 in new sales? Let me show you the numbers. Can we chat tomorrow?",
    
    # Industry/business specific
    "restaurant": "Oh perfect! We LOVE working with restaurants. We can boost your Google rankings so locals find you, create drool-worthy food content for Instagram, and run targeted ads to fill tables during slow hours. One of our restaurant clients went from 40% to 90% capacity in 2 months. Interested?",
    
    "ecommerce": "Ecommerce is our specialty! We optimize product pages for conversions, run Facebook and Google Shopping ads, and create content that turns browsers into buyers. Average order value usually jumps 30-40% after our optimization. What platform are you on - Shopify, WooCommerce?",
    
    "small business": "Small businesses are exactly who we serve best! We get it - every dollar counts. That's why we focus on high-ROI strategies first. Most small business clients start with SEO + Social Media combo. Gets you found AND builds your brand. Should we explore what makes sense for you?",
    
    # Objections/concerns
    "think about it": "Absolutely, take your time! No pressure at all. But quick tip - the businesses that win are the ones that act fast. Your competitors are marketing RIGHT NOW. How about this - let me send you a free marketing audit? Takes me 10 minutes, might show you some quick wins. Can I get your email?",
    
    "maybe later": "Totally understand! But here's the reality - 'later' in marketing usually means lost revenue. Every day you wait is a day your competitor gets YOUR customers. How about we just do a quick 10-minute discovery call? Worst case, you learn something. Best case - we transform your business. Deal?",
    
    "not sure": "No worries! That's exactly why we offer free consultations. No commitment, just value. We'll analyze your current situation, show you opportunities, and if it makes sense, we move forward. If not, at least you got free expert advice. Risk-free! Want to schedule that?",
    
    # Positive responses
    "sounds good": "Awesome! I'm so pumped to work with you. Let me get you booked in for a strategy session. We'll map out exactly how to hit your goals. I'm looking at tomorrow at 2 PM or Friday at 10 AM. Which works better for you?",
    
    "interested": "That's what I love to hear! You're making a smart move. Digital marketing done right is literally a money printer. Let's get you scheduled for a free consultation where we'll build your custom roadmap. This week work for you?",
    
    "yes": "Perfect! You won't regret this. I'll send you a calendar link right after this call. We'll spend 15-30 minutes understanding your business, then I'll show you exactly what Digital Lab can do for you. Expect some serious results! Anything else you want to know?",
    
    # General/filler
    "okay": "Cool! So what's the next step look like for you? Are you ready to elevate your digital presence, or do you have more questions?",
    
    "thanks": "You're so welcome! That's what we're here for. Helping businesses like yours grow is literally why we wake up in the morning. So, ready to take the next step, or want to know more about anything specific?",
    
    "thank you": "My pleasure! We're all about creating success stories. Your business deserves to be seen by the right people. Should we get you booked for that strategy call?",
    
    # Closing phase - referencing previous conversation
    "book call": "Fantastic! I'm excited to dive deeper into how we can help you grow. Based on what we've discussed, I think we can create something really special for your business. I have tomorrow at 2 PM or Friday at 10 AM open. Which works better for you?",
    
    "schedule": "Perfect! Let's lock it in. I'll set up a strategy session where we can map out exactly how to achieve what we talked about. Our CEO will personally walk you through the game plan. What's your email so I can send you the calendar invite?",
    
    "tomorrow": "Tomorrow works great! I'll put you down for 2 PM. You're going to love what we have planned based on everything you've shared. I'll send you a calendar invite right after this call. Looking forward to it!",
    
    "friday": "Friday it is! 10 AM is perfect. Mark your calendar - this is going to be a game-changer for your business based on what we discussed. I'll email you the meeting link and some prep materials. Exciting stuff!",
    
    "2 pm": "2 PM locked in! Based on our conversation today, I'm already thinking of some strategies we can implement right away. You'll get a calendar invite within the next few minutes. Can't wait to show you what we've got!",
    
    "10 am": "10 AM works perfect! I'm pumped to put together a custom plan for you based on what you've told me. Expect an email with the meeting details shortly. This is going to be good!",
    
    "available": "Great question! I've got a few spots this week. Tomorrow at 2 PM or Friday at 10 AM work best. Given everything we've talked about, I think the sooner we get started, the better. Which time suits you?",
    
    "when can we meet": "I love the enthusiasm! Let's get you on the calendar ASAP. I have tomorrow afternoon at 2 PM or Friday morning at 10 AM. Based on our chat, I'm already excited to show you what we can do. Which time works?",
    
    "this week": "Definitely! I want to keep this momentum going. I've got tomorrow at 2 PM and Friday at 10 AM available. Given what you've shared about your goals, I think we should move quickly. What works for you?",
    
    "next week": "I hear you! Next week works too. But here's my honest advice - based on what you've told me, the sooner we get going, the sooner you'll see results. Can I tempt you with a Friday slot this week at 10 AM? Otherwise, I can do Monday or Tuesday next week.",
    
    # Follow-up after booking
    "email": "Perfect! Go ahead and give me your email address. I'll send you the calendar invite along with some prep materials so we can hit the ground running. This is going to be great!",
    
    "phone number": "Sure thing! What's the best number to reach you? I'll text you the meeting details right before our call so you don't miss it. Based on what we discussed, I think you're going to love what we've prepared!",
    
    # Company details
    "website": "Absolutely! Our website is digitallabservices.com - you can check out our portfolio, case studies, and client testimonials there. We also have some free resources that might help you. Want me to send you a link to anything specific?",
    
    "where are you located": "Great question! We work 100% remotely, which is actually perfect for you. We serve both international and local clients from all over the world. No matter where you are, we've got you covered. It's 2024 - location doesn't matter, results do! Where are you based?",
    
    "location": "We're a remote-first agency, so we work with clients globally - both international and local markets. This means we can work in your timezone and you get the benefit of our diverse, worldwide experience. Pretty cool, right? Where's your business located?",
    
    "remote": "Yes! We're fully remote. It's actually one of our strengths - we've worked with clients from New York to Dubai, from small local businesses to international brands. No matter where you are, we deliver the same high-quality results. Makes collaboration super flexible too!",
    
    # Scheduling flexibility
    "not available": "No worries at all! I totally get it - everyone's busy. How about this: I can send you a Calendly link where you can pick any time that works for your schedule. That way, you have full control. Or if you prefer, just let me know what times generally work for you and I'll find something that fits!",
    
    "busy": "I completely understand! Life gets hectic. Here's what I can do - I'll send you a Calendly link so you can schedule at your convenience, or you can just tell me what days/times usually work for you and I'll make it happen. What works better for you?",
    
    "different time": "Absolutely! I want to make this as easy as possible for you. What time zone are you in, and what days/times typically work best? I can also send you our Calendly link if you'd rather just pick a slot yourself. Whatever's easier!",
    
    "can't make it": "No problem! Flexibility is key. Let me send you a Calendly link where you can see all our available slots and pick whatever works for your schedule. Or if you prefer, just throw out some times that work for you and I'll make it happen. Sound good?",
    
    "calendly": "Smart! I'll shoot you our Calendly link right after this call. You can pick any time that fits your schedule - we have slots throughout the week. It's super easy, and you'll get an automatic confirmation. What email should I send it to?",
    
    # Call endings - proper farewells
    "bye": "It's been awesome chatting with you! I'm really excited about what we can do for your business. You'll be hearing from me soon with all the details. Have a fantastic day, and talk to you very soon!",
    
    "goodbye": "Thanks so much for your time today! This was a great conversation. I'm genuinely excited to help you achieve what we talked about. Keep an eye on your inbox - I'll send everything over shortly. Take care and talk soon!",
    
    "that's all": "Perfect! I think we covered everything we needed to. I'm pumped about the next steps based on our conversation today. You'll get a confirmation email from me shortly. Thanks for choosing Digital Lab - we're going to do great things together! Have an amazing day!",
    
    "that's enough": "Sounds good! I appreciate you taking the time to chat. Based on everything we discussed, I'm already mapping out how we can help you succeed. Watch for my email with next steps. Have a great rest of your day, and I'll talk to you soon!",
    
    "end call": "Absolutely! This has been fantastic. I love your vision for where you want to take your business. I'll follow up with all the details we talked about. Thanks again for reaching out to Digital Lab - you made a great choice! Talk to you very soon. Take care!",
    
    "talk later": "For sure! Really appreciate your time today. I'm excited about what's ahead for your business. Keep an eye out for my email - I'll send over everything we discussed plus some bonus materials. Have an excellent day, and we'll connect soon!",
    
    # Default/catchall responses
    "default_1": "That's a great point! You know what, this is exactly the kind of thing we should discuss in detail. A lot depends on your specific situation. How about we jump on a quick call where I can give you personalized answers? I promise it'll be worth your time!",
    
    "default_2": "I love your questions! You're clearly serious about growth. Here's what I suggest - let's get on a brief consultation call. I can answer everything in detail and show you exactly what success looks like for your business. Sound good?",
    
    "default_3": "Great question! Every business is different, which is why we customize everything. Rather than give you a generic answer, let me understand YOUR situation first. Can we schedule a quick discovery call? I promise you'll walk away with value even if we don't work together!"
}

# Keyword matching system for natural conversation flow
def get_demo_response(user_message: str) -> str:
    """
    Match user message to most appropriate scripted response
    Uses keyword detection for natural flow
    """
    message_lower = user_message.lower().strip()
    
    # Direct matches first
    if message_lower in DEMO_SCRIPT:
        return DEMO_SCRIPT[message_lower]
    
    # Keyword-based matching
    keywords_map = {
        ("hi", "hello", "hey"): ["hi", "hello"],
        ("service", "offer", "what do you do", "help with"): ["what services", "services do you offer"],
        ("seo", "search engine", "google ranking", "rank"): ["seo", "search engine"],
        ("social media", "instagram", "facebook", "tiktok"): ["social media", "instagram"],
        ("website", "web dev", "site", "web design"): ["website", "web development"],
        ("video", "editing", "youtube", "reels"): ["video", "video editing"],
        ("price", "cost", "how much", "expensive", "pricing"): ["how much", "cost", "price"],
        ("restaurant", "cafe", "food"): ["restaurant"],
        ("ecommerce", "online store", "shopify"): ["ecommerce"],
        ("small business", "startup", "local business"): ["small business"],
        ("think", "maybe", "not sure"): ["think about it", "maybe later", "not sure"],
        ("good", "great", "sounds good", "interested"): ["sounds good", "interested"],
        ("yes", "yeah", "sure", "ok"): ["yes"],
        ("thanks", "thank you"): ["thanks", "thank you"],
        ("book", "schedule", "call", "meeting", "appointment"): ["book call", "schedule"],
        ("tomorrow"): ["tomorrow"],
        ("friday"): ["friday"],
        ("2 pm", "2pm", "afternoon"): ["2 pm"],
        ("10 am", "10am", "morning"): ["10 am"],
        ("available", "availability", "when", "time"): ["available", "when can we meet"],
        ("this week"): ["this week"],
        ("next week"): ["next week"],
        ("email", "e-mail"): ["email"],
        ("phone", "number", "contact"): ["phone number"],
        ("digitallabservices", "your website", "site link", "url"): ["website"],
        ("where are you", "your location", "office"): ["where are you located", "location"],
        ("remote", "work from home", "virtual"): ["remote"],
        ("not available", "can't make"): ["not available", "can't make it"],
        ("busy", "no time"): ["busy"],
        ("different time", "another time", "reschedule"): ["different time"],
        ("calendly", "calendar link", "scheduling link"): ["calendly"],
        ("bye", "goodbye"): ["bye", "goodbye"],
        ("that's all", "that's it", "all for now"): ["that's all"],
        ("that's enough", "enough for now"): ["that's enough"],
        ("end call", "hang up", "finish"): ["end call"],
        ("talk later", "speak later", "chat later"): ["talk later"]
    }
    
    # Check for keyword matches
    for keywords, script_keys in keywords_map.items():
        if any(keyword in message_lower for keyword in keywords):
            # Return first matching script
            for key in script_keys:
                if key in DEMO_SCRIPT:
                    return DEMO_SCRIPT[key]
    
    # Fallback to default responses (rotate for variety)
    import random
    defaults = ["default_1", "default_2", "default_3"]
    return DEMO_SCRIPT[random.choice(defaults)]
