# Documentation

This application is for collecting various analytics data from [`finki-discord-bot`](https://github.com/finki-hub/finki-discord-bot) usage. At the time of writing, it collects some data about the following informational commands which students are able to call:

- `/faq`: Retrieve a document about FCSE
- `/staff`: Retrieve information about any staff member (name, title, office, etc.)
- `/office`: Retrieve information about any classroom or office within the campus
- `/course`: Retrieve information about any course (name, prerequisite, level, etc.)

Each event has its own data structure, consisting of metadata (user calling the command, command it was called in, etc) and the payload information (the data from the command, i.e. document, office, etc.)

## Tech stack

Uses [`FastAPI`](https://github.com/fastapi/fastapi) for exposing endpoints and [`MongoDB`](https://github.com/mongodb/mongo) for data storage. It was chosen over a relational database due to the fact that the analytics events are unstructured and come as JSON objects with differing schemas and data inside.

The events originate from [`finki-discord-bot`](https://github.com/finki-hub/finki-discord-bot). This app exposes `/events/ingest` for ingesting and `/events/{event_name}` for querying events with options for filtering which the Discord bot uses.

## Pipeline

1. On command execution, collect data and send it to this (analytics) service
2. Save the event in DB
3. Queue the event for further analysis using a background worker
4. If the event is not an FAQ event, terminate here, otherwise continue to the next step
5. In the message context of the event, using an LLM, find the relevant user question
6. If there is no user question, terminate here, otherwise continue to the next step
7. Given the user question, try to find the correct answer (ground truth) within the document
8. If there is no correct answer, terminate here, otherwise continue to the next step
9. In the existing event, save also the user question and correct answer to DB

The events are now available for querying and filtering. The FAQ events with identified questions and answers are used further for evaluating LLMs.

Afterwards, this dataset is used to evaluate a range of models on Macedonian data (the FAQ data with correctly identified questions and answers) and prompts.

[The (current state of the) dataset is available here](https://docs.google.com/spreadsheets/d/1usBMdSTUL7ANRboQk5uvwf4Gh_tL_B-MDLV9kHTuF4Q/edit?usp=sharing).
[The repository for evaluating models is available here](https://github.com/Delemangi/llms-evaluation).

## Related repositories

- Discord bot: [`finki-discord-bot`](https://github.com/finki-hub/finki-discord-bot)
- RAG chat bot: [`finki-chat-bot`](https://github.com/finki-hub/finki-chat-bot)
- Analytics (you are currently here): [`finki-analytics`](https://github.com/finki-hub/finki-analytics)
- Macedonian LLMs evaluation: [`llms-evaluation`](https://github.com/Delemangi/llms-evaluation)

## Examples

### FAQ with correctly identified question & answer

```json
{
  "event_type": "faq",
  "event_id": "29c12611-97c3-4ca6-a6ba-fb415e630f4c",
  "timestamp": "2025-06-23T15:59:22.763361Z",
  "metadata": {
    "callerId": "198249751001563136",
    "channelId": "814540709612486676",
    "commandName": "faq",
    "guildId": "810997107376914444"
  },
  "payload": {
    "content": "Студентската служба е достапна секој работен ден, од **09:00 до 12:00 часот**. Просторијата на Студентската служба се наоѓа во ТМФ, до кабинетот 117.\n\nКонтакт:\n- Електронска пошта: `studentski@finki.ukim.mk`\n- Број: `070 302 440` (ретко работи, само од 13:00 до 15:00 часот)",
    "keyword": "Студентска служба",
    "question": "Студентска служба",
    "context": [
      {
        "authorId": "198249751001563136",
        "content": "kolku chini 1 semestar na magisterski",
        "messageId": "1386733822363832415",
        "timestamp": "2025-06-23T15:45:07.520Z"
      },
      {
        "authorId": "198249751001563136",
        "content": "kade se naogja studentskata sluzba",
        "messageId": "1386737370161741935",
        "timestamp": "2025-06-23T15:59:13.381Z"
      }
    ]
  },
  "extracted_answer": "Просторијата на Студентската служба се наоѓа во ТМФ, до кабинетот 117.",
  "identified_user_question": "kade se naogja studentskata sluzba"
}
```

### Staff

```json
{
  "event_type": "staff",
  "event_id": "83234173-ba43-4fa1-ab7a-f8edb6568d29",
  "timestamp": "2025-06-23T15:59:52.387753Z",
  "metadata": {
    "callerId": "198249751001563136",
    "channelId": "814540709612486676",
    "commandName": "staff",
    "guildId": "810997107376914444"
  },
  "payload": {
    "keyword": "Георгина Мирчева",
    "staff": {
      "cabinet": "Ф12",
      "consultations": "https://consultations.finki.ukim.mk/display/georgina.mirceva",
      "courses": "https://courses.finki.ukim.mk/user/profile.php?id=1464",
      "email": "georgina.mirceva@finki.ukim.mk",
      "name": "Георгина Мирчева",
      "position": "Редовен професор",
      "profile": "https://www.finki.ukim.mk/mk/staff/georgina-mirceva",
      "title": "д-р"
    },
    "context": [
      {
        "authorId": "198249751001563136",
        "content": "kolku chini 1 semestar na magisterski",
        "messageId": "1386733822363832415",
        "timestamp": "2025-06-23T15:45:07.520Z"
      },
      {
        "authorId": "198249751001563136",
        "content": "kade se naogja studentskata sluzba",
        "messageId": "1386737370161741935",
        "timestamp": "2025-06-23T15:59:13.381Z"
      }
    ]
  },
  "extracted_answer": null,
  "identified_user_question": null
}
```

## Pipeline visualization

![Pipeline](./pipeline.png)

## Available documents to search from

- "Дисциплински мерки"
- "Препорачани студентски бенефиции"
- "Што е ФИНКИ"
- "Паузирање на студии"
- "Bugs во iKnow"
- "Изборни предмети од универзитетска листа"
- "Субвенциониран студентски оброк"
- "Запишување 6ти (шести) предмет / над 35 кредити"
- "Деканат"
- "Закаснето пријавување испити (со казна)"
- "Позиции"
- "Листа од дипломски, магистерски и докторски трудови"
- "Закаснет внес на оцена и запишување семестар без оцени"
- "Празен семестар (административно запишување)"
- "Уплатници и ценовник (Финансии)"
- "Испишување (отпишување)"
- "HPC курсеви"
- "Пријавување на испити"
- "Презапишување / повторување"
- "Мирување на студии"
- "Акредитации"
- "Изборни предмети од факултетска листа"
- "Пракса"
- "Промена на квота на студирање"
- "Стратегија за најбрзо дипломирање"
- "Промена на факултет / универзитет"
- "Правила за нивоа на предмети"
- "Промена на предмет"
- "Молби"
- "Подигнување лични документи од упис"
- "Испитни сесии"
- "Академски календар"
- "Пристап до курс"
- "Менување на акредитација од 2018 во 2023"
- "Студентска служба"
- "Факултетско студентско собрание (ФСС)"
- "Административна такса / Таксена марка"
- "Предуслови"
- "Закаснето запишување на семестар"
- "Ослободување од партиципација"
- "Заверување (заверка) на семестар"
- "Архива"
- "Стипендии од МОН"
- "Едуроам (Eduroam)"
- "Промена на професор"
- "Вонредно студирање"
- "Поврат на средства"
- "Невалиден (црвен) предмет / семестар во iKnow"
- "Постапка за дипломирање"
- "Студирање и вработување / пракса"
- "Активирање на предмет"
- "3 (три) / 4 (четири) годишни студии"
- "Продолжување на рок или откажување на дипломска работа"
- "Погрешно потврден упис во iKnow"
- "Потписи"
- "Запишување на семестар"
- "Документи за дипломирање"
- "Уплата и трошоци при запишување на семестар"
- "Поништување на оцена"
- "Компјутерски центар"
- "Прва најава на системот за испити"
- "Запишување предмет без исполнет предуслов"
- "Кредити од екстракурикуларни активности"
- "ЈСП"
- "Потврди и уверенија"
- "Промена на студиска програма (смер)"
- "Контакт и локација"
- "Максимален / Минимален број на кредити и предмети во семестар"
- "Обновување индекс"
- "Студиски програми (Смерови)"
