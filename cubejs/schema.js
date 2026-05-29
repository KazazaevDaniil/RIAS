// Cube.js data schema — Часть 5: Semantic Layer
// Описывает бизнес-метрики и измерения для университетской платформы

cube(`Students`, {
  sql: `SELECT * FROM university.students`,

  measures: {
    count: {
      type: `count`,
      title: `Количество студентов`,
    },
  },

  dimensions: {
    studentId: {
      sql: `student_id`,
      type: `number`,
      primaryKey: true,
    },
    name: {
      sql: `name`,
      type: `string`,
      title: `Имя студента`,
    },
    faculty: {
      sql: `faculty`,
      type: `string`,
      title: `Факультет`,
    },
    groupName: {
      sql: `group_name`,
      type: `string`,
      title: `Группа`,
    },
    enrolledYear: {
      sql: `enrolled_year`,
      type: `number`,
      title: `Год поступления`,
    },
  },
});

cube(`Grades`, {
  sql: `SELECT * FROM university.grades`,

  joins: {
    Students: {
      sql: `${CUBE}.student_id = ${Students}.student_id`,
      relationship: `many_to_one`,
    },
  },

  measures: {
    avgGrade: {
      sql: `grade`,
      type: `avg`,
      title: `Средняя оценка`,
      format: `number`,
    },
    count: {
      type: `count`,
      title: `Количество оценок`,
    },
  },

  dimensions: {
    gradeId: {
      sql: `grade_id`,
      type: `number`,
      primaryKey: true,
    },
    subject: {
      sql: `subject`,
      type: `string`,
      title: `Предмет`,
    },
    faculty: {
      sql: `faculty`,
      type: `string`,
      title: `Факультет`,
    },
    groupName: {
      sql: `group_name`,
      type: `string`,
      title: `Группа`,
    },
    gradeDate: {
      sql: `grade_date`,
      type: `time`,
      title: `Дата оценки`,
    },
  },
});

cube(`RoomOccupancy`, {
  sql: `SELECT * FROM university.room_occupancy`,

  measures: {
    avgOccupancy: {
      sql: `count`,
      type: `avg`,
      title: `Среднее заполнение`,
    },
    totalVisits: {
      sql: `count`,
      type: `sum`,
      title: `Всего визитов`,
    },
  },

  dimensions: {
    room: {
      sql: `room`,
      type: `string`,
      title: `Аудитория`,
    },
    campus: {
      sql: `campus`,
      type: `string`,
      title: `Корпус`,
    },
    windowStart: {
      sql: `window_start`,
      type: `time`,
      title: `Начало окна`,
    },
  },
});
