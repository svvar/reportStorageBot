from sqlalchemy import Column, Integer, String, Float, DateTime, NUMERIC, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import sqlalchemy as sa
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

Base = declarative_base()
engine = create_async_engine('sqlite+aiosqlite:///reports.sqlite')


class Projects(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Project {self.name}>'


class SumData(Base):
    __tablename__ = 'sum_data'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    datetime = Column(DateTime, default=datetime.datetime.now())
    sum = Column(NUMERIC(12, 2))

    def __repr__(self):
        return f'<SumData {self.project_id} {self.sum} {self.datetime}>'


class Reports(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    datetime = Column(DateTime, default=datetime.datetime.now())

    def __repr__(self):
        return f'<Report {self.project_id} {self.datetime}>'


async def get_projects_count():
    async with AsyncSession(engine) as session:
        result = await session.execute(sa.select(sa.func.count(Projects.id)))
        return result.scalar()


async def get_projects(limit=None, offset=None):
    async with AsyncSession(engine) as session:
        if limit and offset:
            result = await session.execute(sa.select(Projects).limit(limit).offset(offset))
        elif limit:
            result = await session.execute(sa.select(Projects).limit(limit))
        elif offset:
            result = await session.execute(sa.select(Projects).offset(offset))
        else:
            result = await session.execute(sa.select(Projects))
        return result.scalars().all()


async def add_project(name):
    async with AsyncSession(engine) as session:
        async with session.begin():
            new_project = Projects(name=name)
            session.add(new_project)
        await session.commit()


async def save_sum(project_id, sum):
    async with AsyncSession(engine) as session:
        async with session.begin():
            new_sum = SumData(project_id=project_id, sum=sum)
            session.add(new_sum)
        await session.commit()


async def get_last_report_date(project_id):
    async with AsyncSession(engine) as session:
        result = await session.execute(sa.select(Reports).filter(Reports.project_id == project_id).order_by(Reports.datetime.desc()).limit(1))
        scalar = result.scalars().first()
        if scalar:
            return scalar.datetime
        else:
            return None


async def update_report_date(project_id):
    async with AsyncSession(engine) as session:
        async with session.begin():
            new_report = Reports(project_id=project_id)
            session.add(new_report)
        await session.commit()


async def get_sums_by_date(project_id, start_date=None):
    async with AsyncSession(engine) as session:
        if start_date:
            result = await session.execute(
                sa.select(Projects.name, SumData.datetime, SumData.sum)
                .select_from(SumData)
                .join(Projects)
                .filter(SumData.project_id == project_id, SumData.datetime >= start_date))
        else:
            result = await session.execute(
                sa.select(Projects.name, SumData.datetime, SumData.sum)
                .select_from(SumData)
                .join(Projects)
                .filter(SumData.project_id == project_id))

        return result.all()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main():
    await create_tables()

if __name__ == '__main__':
    asyncio.run(main())