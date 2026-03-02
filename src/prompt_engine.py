"""Prompt template manager for generating themed prompts."""
import random
from pathlib import Path
from typing import List, Optional
import config


class PromptEngine:
    """Manages prompt templates organized by gender and theme."""
    
    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or config.PROMPTS_DIR
        self._cache = {}  # Cache loaded prompts
        
    def _get_prompt_file(self, gender: str, theme: str) -> Path:
        """Get the path to a prompt file."""
        return self.prompts_dir / gender / f"{theme}.txt"
    
    def _load_prompts(self, gender: str, theme: str) -> List[str]:
        """Load prompts from file, with caching."""
        cache_key = f"{gender}/{theme}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        prompt_file = self._get_prompt_file(gender, theme)
        
        if not prompt_file.exists():
            # Try to use fallback prompts
            prompts = self._get_fallback_prompts(gender, theme)
        else:
            with open(prompt_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Split by blank lines or newlines, filter empty lines
                prompts = [p.strip() for p in content.split("\n") if p.strip()]
        
        self._cache[cache_key] = prompts
        return prompts
    
    def _get_fallback_prompts(self, gender: str, theme: str) -> List[str]:
        """Get fallback prompts if file doesn't exist."""
        # Generic prompts that work for any gender/theme
        base_prompts = [
            f"professional portrait photography, {theme} style, high quality, detailed, 8k",
            f"aesthetic portrait, {theme} aesthetic, beautiful lighting, artistic composition",
            f"editorial photography, {theme} vibes, stunning visual, professional quality",
            f"portrait shot, {theme} atmosphere, cinematic quality, detailed features",
            f"professional photoshoot, {theme} theme, high fashion, beautiful lighting",
        ]
        return base_prompts
    
    def get_random_prompt(self, gender: str, theme: str) -> str:
        """Get a random prompt for the specified gender and theme."""
        prompts = self._load_prompts(gender, theme)
        
        if not prompts:
            raise ValueError(f"No prompts available for {gender}/{theme}")
        
        return random.choice(prompts)
    
    def get_prompts(self, gender: str, theme: str, count: int) -> List[str]:
        """Get multiple unique prompts for the specified gender and theme."""
        prompts = self._load_prompts(gender, theme)
        
        if not prompts:
            raise ValueError(f"No prompts available for {gender}/{theme}")
        
        # If we need more prompts than available, we'll cycle through with variations
        selected = []
        available = prompts.copy()
        
        while len(selected) < count:
            if available:
                prompt = random.choice(available)
                available.remove(prompt)
                selected.append(prompt)
            else:
                # Cycle through with seed variations
                prompt = random.choice(prompts)
                selected.append(prompt)
        
        return selected
    
    def get_available_themes(self, gender: str) -> List[str]:
        """Get list of available themes for a gender."""
        gender_dir = self.prompts_dir / gender
        
        if not gender_dir.exists():
            return list(config.THEMES.keys())
        
        themes = []
        for file in gender_dir.glob("*.txt"):
            themes.append(file.stem)
        
        return themes if themes else list(config.THEMES.keys())
    
    def theme_exists(self, gender: str, theme: str) -> bool:
        """Check if a theme exists for a gender."""
        return self._get_prompt_file(gender, theme).exists()


def create_prompt_template(gender: str, theme: str, prompts: List[str]) -> None:
    """Create a prompt template file.
    
    Args:
        gender: "male" or "female"
        theme: Theme name
        prompts: List of prompt strings
    """
    theme_dir = config.PROMPTS_DIR / gender
    theme_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_file = theme_dir / f"{theme}.txt"
    
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write("\n\n".join(prompts))


# Default prompt templates for initialization
DEFAULT_PROMPTS = {
    "male": {
        "cinematic": [
            "A man standing on a rooftop at golden hour, cinematic lighting, film grain, 35mm lens, dramatic shadows, movie poster aesthetic, professional photography, 8k quality, moody atmosphere",
            "A man walking through neon-lit city streets at night, cinematic color grading, anamorphic lens flare, cyberpunk vibes, rain-slicked pavement reflections, editorial style",
            "Portrait of a man in dramatic side lighting, cinematic composition, shallow depth of field, film noir aesthetic, high contrast, professional portrait photography",
            "A man sitting in a vintage leather chair, cinematic warm tones, window light streaming in, classic Hollywood portrait style, detailed textures, 8k resolution",
            "A man looking out at city skyline from high-rise balcony, cinematic wide shot, blue hour lighting, atmospheric haze, professional cinematography style",
            "A man in a tailored suit walking down grand staircase, cinematic framing, dramatic shadows, architectural beauty, film grain texture, editorial fashion",
            "Portrait of a man in rain, cinematic mood, umbrella silhouette, street lights bokeh, melancholic atmosphere, professional photography",
            "A man driving vintage car at sunset, cinematic color palette, lens flare, open road, freedom aesthetic, movie still quality",
            "A man standing in foggy forest, cinematic mystery, volumetric lighting, ethereal atmosphere, professional nature cinematography",
            "A man at a jazz club, cinematic warm lighting, saxophone in background, film grain, 1950s aesthetic, moody portrait",
            "A man on motorcycle at night, cinematic motion blur, city lights trailing, leather jacket, rebel aesthetic, professional action photography",
            "A man reading in old library, cinematic dust motes in light beams, vintage atmosphere, intellectual aesthetic, warm tones",
            "A man standing on train platform, cinematic composition, steam from train, nostalgic atmosphere, film photography style",
            "A man in industrial warehouse, cinematic dramatic lighting, exposed brick, artistic shadows, urban exploration aesthetic",
            "A man at beach bonfire, cinematic golden hour, sparks flying, warmth and friendship, professional lifestyle photography",
        ],
        "vintage": [
            "A man in 1950s style, vintage film look, faded colors, classic portrait, retro aesthetic, analog photography feel",
            "A man with vintage car, 1970s aesthetic, film grain, warm tones, nostalgic atmosphere, classic American style",
            "Portrait of a man in vintage denim jacket, 90s aesthetic, faded colors, grainy texture, retro fashion photography",
            "A man at old diner, vintage neon signs, 1960s vibe, film photography style, warm color grading, nostalgic mood",
            "A man with vinyl records, vintage music aesthetic, 1980s style, film grain, warm lighting, retro portrait",
            "A man in classic barbershop, vintage grooming aesthetic, 1950s style, warm tones, traditional masculinity",
            "A man with vintage camera, photographer aesthetic, 1970s style, film photography, artistic vintage portrait",
            "A man in retro bowling alley, 1960s aesthetic, vintage colors, fun nostalgic vibe, film grain texture",
            "A man with vintage motorcycle, greaser style, 1950s aesthetic, leather jacket, retro cool, film photography",
            "A man in old train station, vintage travel aesthetic, 1940s style, sepia tones, nostalgic journey feeling",
            "A man with vintage radio, mid-century modern aesthetic, 1960s style, warm interior, retro technology",
            "A man in classic boxing gym, vintage sports aesthetic, 1970s style, film grain, determined expression",
            "A man with vintage typewriter, writer aesthetic, 1950s style, intellectual vibe, warm lighting, retro office",
            "A man in retro pool hall, 1980s aesthetic, vintage colors, film photography style, cool casual vibe",
            "A man with vintage surfboard, 1960s beach aesthetic, faded colors, sun-bleached look, retro California style",
        ],
        "beach": [
            "A man walking on tropical beach at sunset, golden hour lighting, relaxed vibe, ocean waves, summer aesthetic",
            "A man sitting on beach rocks, coastal atmosphere, natural lighting, contemplative mood, seaside portrait",
            "A man playing beach volleyball, action shot, sunny day, athletic aesthetic, summer sports, dynamic composition",
            "A man at beach bonfire with friends, warm firelight, starry sky, summer night, friendship and warmth",
            "A man surfing at sunrise, silhouette against sun, ocean spray, adventurous spirit, surf culture aesthetic",
            "A man walking barefoot on wet sand, footprints trailing, ocean waves, peaceful morning, beachcomber vibe",
            "A man reading under beach umbrella, relaxed vacation mood, tropical setting, leisure aesthetic, summer reading",
            "A man at beach cliff overlook, dramatic coastal scenery, wind in hair, adventurous pose, ocean backdrop",
            "A man building sandcastle, playful beach mood, sunny day, childhood nostalgia, summer fun aesthetic",
            "A man doing yoga on beach at sunrise, wellness aesthetic, peaceful morning, mindfulness, beach meditation",
            "A man fishing at pier, coastal lifestyle, early morning light, patient waiting, maritime aesthetic",
            "A man at beach cafe, tropical drinks, relaxed atmosphere, vacation mode, coastal dining aesthetic",
            "A man snorkeling in clear water, underwater adventure, tropical fish, marine exploration, ocean discovery",
            "A man at beach sunset party, golden hour celebration, summer vibes, tropical music, festive atmosphere",
            "A man walking through beach dunes, sea grass swaying, coastal landscape, serene nature, beach exploration",
        ],
        "streetwear": [
            "A man in urban alleyway, streetwear fashion, graffiti wall backdrop, contemporary style, urban photography",
            "A man on city rooftop, streetwear aesthetic, skyline view, modern fashion, urban exploration vibe",
            "A man at skate park, streetwear style, skateboard culture, dynamic pose, urban sports aesthetic",
            "A man in neon-lit street, streetwear fashion, night city vibes, contemporary urban style, bold colors",
            "A man with street art mural, streetwear aesthetic, colorful backdrop, urban culture, artistic fashion",
            "A man at basketball court, streetwear style, urban sports, athletic aesthetic, city playground",
            "A man in subway station, streetwear fashion, urban transit, gritty aesthetic, metropolitan style",
            "A man at urban coffee shop, streetwear casual, city lifestyle, contemporary cafe culture, relaxed vibe",
            "A man on motorcycle in city, streetwear style, urban mobility, leather and denim, city rider aesthetic",
            "A man at concert venue, streetwear fashion, music culture, event atmosphere, contemporary entertainment",
            "A man in industrial district, streetwear aesthetic, warehouse backdrop, urban exploration, modern grit",
            "A man at street market, streetwear style, urban commerce, colorful stalls, city life atmosphere",
            "A man on bridge at night, streetwear fashion, city lights backdrop, urban architecture, night photography",
            "A man at urban gym, streetwear athletic, fitness culture, modern training, health and style",
            "A man in city park, streetwear casual, urban nature, contemporary outdoor, city green space",
        ],
    },
    "female": {
        "cinematic": [
            "A woman standing on balcony at golden hour, cinematic lighting, flowing dress, wind in hair, movie poster aesthetic",
            "A woman walking through rain-soaked streets, cinematic atmosphere, umbrella silhouette, neon reflections, film noir style",
            "Portrait of a woman in dramatic window light, cinematic composition, elegant shadows, classic Hollywood glamour",
            "A woman in vintage convertible at sunset, cinematic color grading, freedom and adventure, film grain texture",
            "A woman standing in field at blue hour, cinematic wide shot, ethereal atmosphere, flowing fabric, dreamlike quality",
            "A woman at grand piano in mansion, cinematic luxury, dramatic lighting, elegant atmosphere, high society aesthetic",
            "A woman looking out rain-streaked window, cinematic mood, contemplative portrait, soft focus, emotional atmosphere",
            "A woman dancing in empty ballroom, cinematic elegance, dust motes in light beams, vintage glamour, artistic composition",
            "A woman on train platform in mist, cinematic mystery, vintage luggage, nostalgic journey, film photography style",
            "A woman in rooftop garden at night, cinematic city lights backdrop, intimate atmosphere, urban oasis, romantic lighting",
            "A woman reading in library ladder, cinematic intellectual aesthetic, warm lighting, vintage books, scholarly elegance",
            "A woman at beach during storm, cinematic drama, waves crashing, windswept hair, powerful nature backdrop",
            "A woman in art gallery, cinematic culture, dramatic lighting on artwork, sophisticated atmosphere, refined aesthetic",
            "A woman walking through autumn leaves, cinematic seasonal beauty, golden light, falling leaves, nostalgic mood",
            "A woman at jazz club bar, cinematic nightlife, warm ambient lighting, sophisticated atmosphere, evening elegance",
        ],
        "vintage": [
            "A woman in 1950s dress, vintage fashion, classic portrait, retro aesthetic, film photography, feminine elegance",
            "A woman with vintage bicycle, 1960s style, summer dress, nostalgic atmosphere, warm film tones",
            "Portrait of a woman in vintage tea room, 1940s aesthetic, elegant hat, refined atmosphere, classic femininity",
            "A woman at vintage drive-in, 1950s style, classic car, retro fashion, nostalgic American aesthetic",
            "A woman with vintage suitcase, 1920s travel aesthetic, sepia tones, adventurous spirit, classic journey",
            "A woman in vintage flower shop, 1960s style, colorful blooms, romantic atmosphere, retro charm",
            "A woman at vintage carousel, 1950s fun fair, colorful lights, nostalgic joy, childhood memories",
            "A woman in vintage kitchen, 1950s domestic aesthetic, pastel colors, retro appliances, domestic elegance",
            "A woman with vintage books, 1940s intellectual style, library setting, scholarly aesthetic, literary charm",
            "A woman at vintage beach, 1960s swimwear, sunbathing aesthetic, retro summer, warm film colors",
            "A woman in vintage theater, 1940s glamour, velvet seats, dramatic lighting, classic entertainment",
            "A woman with vintage perfume bottles, 1950s vanity, elegant beauty routine, retro femininity, soft lighting",
            "A woman at vintage train station, 1930s travel, elegant luggage, departure romance, nostalgic journey",
            "A woman in vintage garden party, 1960s social event, floral dress, afternoon tea, retro socialite",
            "A woman with vintage record player, 1970s music aesthetic, vinyl collection, retro entertainment, warm tones",
        ],
        "beach": [
            "A woman walking on tropical beach at sunset, flowing sundress, golden hour glow, ocean breeze, summer romance",
            "A woman sitting on beach swing, tropical paradise, palm trees, relaxed vacation mood, island aesthetic",
            "A woman at beach yoga session, sunrise wellness, peaceful meditation, ocean backdrop, mindful summer",
            "A woman collecting seashells, beachcomber aesthetic, summer activity, shoreline exploration, natural beauty",
            "A woman reading in beach hammock, tropical relaxation, shaded comfort, vacation reading, leisure aesthetic",
            "A woman at beach cliff for sunset, dramatic coastal view, wind in hair, golden light, nature appreciation",
            "A woman doing beach workout, summer fitness, ocean backdrop, active lifestyle, healthy vacation",
            "A woman at tropical beach bar, summer cocktails, relaxed atmosphere, vacation mode, island nightlife",
            "A woman walking through shallow waves, beach stroll, summer dress, playful water, carefree vacation",
            "A woman at beach bonfire party, summer night warmth, friendship circle, starry sky, beach celebration",
            "A woman snorkeling in coral reef, underwater exploration, marine life, tropical adventure, ocean discovery",
            "A woman at beach massage, tropical spa, relaxation, palm shade, vacation wellness, serene atmosphere",
            "A woman building sand sculpture, beach creativity, summer fun, artistic sandcastle, playful vacation",
            "A woman at beach fruit stand, tropical market, fresh coconuts, island culture, summer refreshment",
            "A woman watching sunrise from beach, morning meditation, peaceful dawn, new beginnings, serene ocean",
        ],
        "streetwear": [
            "A woman in urban rooftop, streetwear fashion, city skyline, contemporary style, confident pose, urban aesthetic",
            "A woman at skate park, streetwear style, skate culture, dynamic energy, urban sports fashion",
            "A woman in graffiti alley, streetwear aesthetic, colorful mural backdrop, urban art, bold fashion",
            "A woman at night market, streetwear casual, neon lights, urban commerce, contemporary city life",
            "A woman on city bike, streetwear mobility, urban transport, active lifestyle, metropolitan fashion",
            "A woman at urban cafe, streetwear chic, coffee culture, city lifestyle, contemporary casual",
            "A woman in industrial loft, streetwear aesthetic, exposed brick, urban living, modern interior",
            "A woman at music festival, streetwear fashion, concert vibes, crowd energy, contemporary entertainment",
            "A woman on subway platform, streetwear urban, transit aesthetic, city commute, metropolitan style",
            "A woman at basketball court, streetwear athletic, urban sports, confident pose, city playground",
            "A woman in vintage shop district, streetwear shopping, urban retail, contemporary consumer, city exploration",
            "A woman at rooftop party, streetwear evening, city lights, social atmosphere, urban nightlife",
            "A woman in urban garden, streetwear nature, city green space, contemporary outdoor, park aesthetic",
            "A woman at street food vendor, streetwear casual, urban dining, food culture, city flavors",
            "A woman on city bridge, streetwear fashion, urban architecture, metropolitan landmark, confident stance",
        ],
    },
}


def initialize_default_prompts() -> None:
    """Create default prompt template files if they don't exist."""
    for gender, themes in DEFAULT_PROMPTS.items():
        for theme, prompts in themes.items():
            prompt_file = config.PROMPTS_DIR / gender / f"{theme}.txt"
            if not prompt_file.exists():
                create_prompt_template(gender, theme, prompts)


# Initialize prompts on module load
initialize_default_prompts()