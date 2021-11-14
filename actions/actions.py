# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from python_chefkoch import chefkoch
from rasa_sdk import Action, Tracker
from rasa_sdk.events import FollowupAction
from rasa_sdk.executor import CollectingDispatcher
from duckling import language, DucklingWrapper
import Levenshtein

d = DucklingWrapper()
d.language = language.Language.GERMAN

memory = dict()


class Utils:

    @staticmethod
    def add_to_memory(tracker):
        if tracker.current_state()["sender_id"] not in memory:
            memory[tracker.current_state()["sender_id"]] = dict()

    @staticmethod
    def to_number(entity):
        return d.parse_number(entity["value"])[0]["value"]["value"]


class ActionSpecificRecipe(Action):

    def name(self) -> Text:
        return "action_specific_recipe"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        Utils.add_to_memory(tracker)
        entities = tracker.latest_message["entities"]

        search_term = ""
        difficulty = ""
        amount_of_ppl = 2

        for entity in entities:
            if entity["entity"] == "meal":
                search_term += (entity['value'] + " ")
            elif entity["entity"] == "amount_ppl":
                try:
                    amount_of_ppl = Utils.to_number(entity)
                    dispatcher.utter_message(text=f"Ich habe {amount_of_ppl} Leute als input erkannt")
                except IndexError:
                    pass
            elif entity["entity"] == "difficulty":
                # TODO
                print(entity["value"])

        if not search_term:
            dispatcher.utter_message(text=f"Ich habe leider kein Gericht erkannt.")
            return []

        if "to_select" in memory[tracker.current_state()["sender_id"]] and \
            max([Levenshtein.distance(search_term, memory_term)
                 for memory_term in memory[tracker.current_state()["sender_id"]]["to_select"]]) < 30:

            return [FollowupAction()]

        recipes = chefkoch.search(search_term, frm=0, to=30)

        amount_recipes = len(recipes)
        if amount_recipes >= 3:
            dispatcher.utter_message(text=f"Hier die Top 3 Rezepte für {search_term}")
        elif amount_recipes > 0:
            dispatcher.utter_message(text=f"Hier die Top {amount_recipes} Rezepte für {search_term}")
        else:
            dispatcher.utter_message(text="Ich habe leider keine Rezepte zu deiner Anfrage gefunden.")
            del memory[tracker.current_state()["sender_id"]]["to_select"]
            return []

        memory[tracker.current_state()["sender_id"]]["to_select"] = []

        for recipe in recipes[:3]:
            dispatcher.utter_message(recipe.title + " - " + str(recipe.rating) + " Sterne")
            dispatcher.utter_image_url(recipe.image)
            memory[tracker.current_state()["sender_id"]]["to_select"].append(recipe.title)

        del recipes[:3]

        memory[tracker.current_state()["sender_id"]]["all_recipes"] = recipes

        return []


class More(Action):

    def name(self) -> Text:
        return "action_more"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        Utils.add_to_memory(tracker)

        if "all_recipes" in memory[tracker.current_state()["sender_id"]]:

            if len(memory[tracker.current_state()["sender_id"]]["all_recipes"]) == 0:
                dispatcher.utter_message("Ich habe keine weiteren Rezepte mehr gefunden")
                del memory[tracker.current_state()["sender_id"]]["all_recipes"]

            else:
                for recipe in memory[tracker.current_state()["sender_id"]]["all_recipes"][:3]:
                    dispatcher.utter_message(recipe.title)
                    dispatcher.utter_image_url(recipe.image)

                del memory[tracker.current_state()["sender_id"]]["all_recipes"][:3]
        else:
            # TODO
            dispatcher.utter_message("DU KLEINER HURENSOHN ICH FICKE DEINE ELTERN UND DEINEN HUND. SUCHE NACH NEN FUCKING REZEPT ODER ICH SCHLITZ DIR UND DEINER SCHWESTER HEUTE ABEND DIE KEHLE AUF")

        return []


class SelectRecipe(Action):

    def name(self) -> Text:
        return "action_select"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        Utils.add_to_memory(tracker)






        return []


class ActionMealOfTheDay(Action):

    def name(self) -> Text:
        return "action_meal_of_the_day"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message["entities"]
        if entities[0]["entity"] == "bake":
            meals_of_the_day = chefkoch.get_daily_recommendations(0, 2, "backe")
        else:
            meals_of_the_day = chefkoch.get_daily_recommendations()

        dispatcher.utter_message(text=f"Hier sind die Top 3 Rezepte des Tages")

        for meal in meals_of_the_day:
            dispatcher.utter_message(meal.title)
            dispatcher.utter_image_url(meal.image)

        return []
